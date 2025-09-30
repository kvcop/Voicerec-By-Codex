"""Tests for meeting API endpoints."""

import asyncio
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Annotated, NoReturn, Self, cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import meeting
from app.core.security import create_access_token, hash_password
from app.core.settings import DEFAULT_RAW_AUDIO_DIR, get_settings
from app.db.repositories import MeetingRepository, TranscriptRepository
from app.db.repositories.user import UserRepository
from app.models.meeting import MeetingStatus
from app.services.auth import AUTH_SCHEME_BEARER
from app.services.meeting_processing import MeetingEvent, MeetingProcessingResult
from app.services.transcript import (
    MeetingNotFoundError,
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
)

if TYPE_CHECKING:  # pragma: no cover - imports for type hints
    from fastapi import FastAPI

    from app.models.user import User
    from app.services.meeting_processing import MeetingProcessingService

OverrideMap = dict[Callable[..., object], Callable[..., object]]

AUTH_HEADER_NAME = 'Authorization'
BEARER_PREFIX = AUTH_SCHEME_BEARER.capitalize()


class _RecordingProcessor:
    """Return a predetermined processing result while tracking invocations."""

    def __init__(self, result: MeetingProcessingResult) -> None:
        self._result = result
        self.calls: list[Path] = []

    async def process(self, audio_path: Path) -> MeetingProcessingResult:
        self.calls.append(Path(audio_path))
        return self._result


class _TestTranscriptService(TranscriptService):
    """Test-friendly transcript service that resets session transactions."""

    async def _persist_processing_result(
        self, meeting_uuid: UUID, result: MeetingProcessingResult
    ) -> None:
        await self.session.rollback()
        repository = MeetingRepository(self.session)
        transcript_repository = TranscriptRepository(self.session)

        async with self.session.begin():
            meeting = await repository.get_by_id(meeting_uuid)
            if meeting is None:
                raise MeetingNotFoundError(str(meeting_uuid))
            await self._delete_existing_transcripts(meeting_uuid)
            await self._store_transcript_events(
                meeting,
                meeting_uuid,
                result,
                transcript_repository,
            )
            await repository.update(
                meeting,
                status=MeetingStatus.COMPLETED,
                summary=self._normalize_summary(result.summary),
            )


@contextmanager
def _override_dependencies(app: 'FastAPI', overrides: OverrideMap) -> Iterator[None]:
    """Temporarily apply dependency overrides for the FastAPI app."""
    app.dependency_overrides.update(overrides)
    try:
        yield
    finally:
        for dependency in overrides:
            app.dependency_overrides.pop(dependency, None)


@asynccontextmanager
async def _override_transcript_dependencies(
    app: 'FastAPI',
    raw_audio_dir: Path,
    processor: object,
) -> AsyncIterator[None]:
    """Apply overrides for transcript service and ensure cleanup."""

    def _build_service(
        session: Annotated[AsyncSession, Depends(get_session)],
        client_type: str | None = None,
        gpu_settings: object | None = None,
        raw_audio_dir_override: Path | None = None,
        enforce_audio_presence: bool | None = None,
    ) -> TranscriptService:
        del client_type, gpu_settings, enforce_audio_presence
        directory = raw_audio_dir if raw_audio_dir_override is None else raw_audio_dir_override
        return _TestTranscriptService(
            session,
            cast('MeetingProcessingService', processor),
            raw_audio_dir=directory,
        )

    overrides: OverrideMap = {
        meeting.get_raw_audio_dir: lambda: raw_audio_dir,
        meeting.get_transcript_service: _build_service,
    }
    with _override_dependencies(app, overrides):
        yield None


async def _build_auth_headers(session: AsyncSession) -> tuple[dict[str, str], 'User']:
    """Create authorization headers for a newly provisioned user."""
    repository = UserRepository(session)
    email = f'meeting-{uuid4().hex}@example.com'
    user = await repository.create(email=email, hashed_password=hash_password('SecurePass123'))
    await session.commit()
    token = create_access_token(subject=str(user.id), additional_claims={'email': user.email})
    return {AUTH_HEADER_NAME: f'{BEARER_PREFIX} {token}'}, user


def test_raw_audio_dir_default_location(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default raw audio storage path resides under repository data/raw."""
    monkeypatch.delenv('RAW_AUDIO_DIR', raising=False)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://example')
    monkeypatch.setenv('GPU_GRPC_HOST', 'host')
    monkeypatch.setenv('GPU_GRPC_PORT', '1234')
    monkeypatch.setenv('AUTH_SECRET_KEY', 'integration-secret-key')

    get_settings.cache_clear()
    raw_dir = resolve_raw_audio_dir()
    try:
        assert raw_dir == DEFAULT_RAW_AUDIO_DIR
        assert 'backend' not in raw_dir.parts
        assert raw_dir.is_dir()
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_upload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Uploading audio saves file and returns meeting id."""
    monkeypatch.setattr(meeting, 'CHUNK_SIZE', 1024)

    data = bytes(range(256)) * 4096

    class _AsyncFile:
        def __init__(self, path: Path) -> None:
            self.path = Path(path)
            self._file = self.path.open('wb')
            self.closed = False

        async def write(self, chunk: bytes) -> None:
            self._file.write(chunk)

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            self._file.close()
            self.closed = True

    opened_files: list[_AsyncFile] = []

    def _fake_open(path: Path, mode: str = 'r') -> _AsyncFile:
        assert mode == 'wb'
        async_file = _AsyncFile(Path(path))
        opened_files.append(async_file)
        return async_file

    monkeypatch.setattr(meeting.aiofiles, 'open', _fake_open)

    client = TestClient(fastapi_app)
    headers, user = await _build_auth_headers(fastapi_db_session)
    overrides: OverrideMap = {meeting.get_raw_audio_dir: lambda: tmp_path}
    with _override_dependencies(fastapi_app, overrides):
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('audio.wav', data, 'audio/wav')},
            headers=headers,
        )
    assert response.status_code == HTTPStatus.OK, response.json()
    response_data = response.json()
    meeting_id = response_data['meeting_id']
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == data
    assert opened_files
    assert opened_files[0].closed is True

    repository = MeetingRepository(fastapi_db_session)
    stored_meeting = await repository.get_by_id(UUID(meeting_id))
    assert stored_meeting is not None
    assert stored_meeting.user_id == user.id
    assert stored_meeting.filename == 'audio.wav'


@pytest.mark.asyncio
async def test_upload_rejects_non_wav(
    tmp_path: Path,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Uploading non-WAV files is rejected with 415 status."""
    client = TestClient(fastapi_app)
    headers, _ = await _build_auth_headers(fastapi_db_session)
    overrides: OverrideMap = {meeting.get_raw_audio_dir: lambda: tmp_path}
    with _override_dependencies(fastapi_app, overrides):
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('notes.txt', b'123', 'text/plain')},
            headers=headers,
        )

    assert response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE, response.json()
    assert response.json() == {'detail': 'Only WAV audio is supported.'}
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
async def test_upload_accepts_mixed_case_mime(
    tmp_path: Path,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Mixed-case WAV MIME types are accepted."""
    client = TestClient(fastapi_app)
    headers, _ = await _build_auth_headers(fastapi_db_session)
    overrides: OverrideMap = {meeting.get_raw_audio_dir: lambda: tmp_path}
    with _override_dependencies(fastapi_app, overrides):
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('audio.wav', b'abc', 'audio/WAV')},
            headers=headers,
        )

    assert response.status_code == HTTPStatus.OK, response.json()
    assert 'meeting_id' in response.json()
    assert list(tmp_path.iterdir())


@pytest.mark.asyncio
async def test_upload_streams_large_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Large uploads are streamed to disk without buffering entire payload."""
    monkeypatch.setattr(meeting, 'CHUNK_SIZE', 1024)

    chunks = [b'a' * 1024, b'b' * 1024, b'c']
    writes: list[bytes] = []

    class _AsyncFile:
        def __init__(self, path: Path) -> None:
            self.path = Path(path)
            self._file = self.path.open('wb')
            self.closed = False

        async def write(self, chunk: bytes) -> None:
            writes.append(chunk)
            self._file.write(chunk)

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            self._file.close()
            self.closed = True

    def _fake_open(path: Path, mode: str = 'r') -> _AsyncFile:
        assert mode == 'wb'
        return _AsyncFile(Path(path))

    async def _fake_iter(
        upload: UploadFile | None = None,
        *,
        chunk_size: int = meeting.CHUNK_SIZE,
    ) -> AsyncGenerator[bytes, None]:
        del upload
        assert chunk_size == meeting.CHUNK_SIZE
        for chunk in chunks:
            yield chunk

    monkeypatch.setattr(meeting.aiofiles, 'open', _fake_open)
    monkeypatch.setattr(meeting, '_iter_upload_file', _fake_iter)

    client = TestClient(fastapi_app)
    headers, _ = await _build_auth_headers(fastapi_db_session)
    overrides: OverrideMap = {meeting.get_raw_audio_dir: lambda: tmp_path}
    with _override_dependencies(fastapi_app, overrides):
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('audio.wav', b'dummy', 'audio/wav')},
            headers=headers,
        )

    assert response.status_code == HTTPStatus.OK, response.json()
    meeting_id = response.json()['meeting_id']
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == b''.join(chunks)
    assert writes == chunks


@pytest.mark.asyncio
async def test_stream(
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """SSE endpoint streams transcript fragments and summary events."""

    class _FakeTranscriptService:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def ensure_audio_available(self, meeting_id: str) -> None:
            del meeting_id

        async def stream_transcript(
            self, meeting_id: str
        ) -> AsyncGenerator[dict[str, object], None]:
            self.calls.append(meeting_id)
            yield {'event': 'transcript', 'data': {'speaker': 'A', 'text': 'hello'}}
            yield {'event': 'transcript', 'data': {'speaker': 'B', 'text': 'world'}}
            yield {'event': 'summary', 'data': {'summary': 'Done'}}

    fake_service = _FakeTranscriptService()
    client = TestClient(fastapi_app)
    headers, user = await _build_auth_headers(fastapi_db_session)
    repository = MeetingRepository(fastapi_db_session)
    stored_meeting = await repository.create(user_id=user.id, filename='audio.wav')
    await fastapi_db_session.commit()
    meeting_id = str(stored_meeting.id)
    overrides: OverrideMap = {get_transcript_service: lambda: fake_service}
    lines: list[str] = []
    with (
        _override_dependencies(fastapi_app, overrides),
        client.stream('GET', f'/api/meeting/{meeting_id}/stream', headers=headers) as response,
    ):
        assert response.status_code == HTTPStatus.OK, response.json()
        lines = [line for line in response.iter_lines() if line != '']

    assert lines == [
        'event: transcript',
        'data: {"speaker": "A", "text": "hello"}',
        'event: transcript',
        'data: {"speaker": "B", "text": "world"}',
        'event: summary',
        'data: {"summary": "Done"}',
    ]
    assert fake_service.calls == [meeting_id]


@pytest.mark.asyncio
async def test_stream_missing_meeting_returns_404(
    tmp_path: Path,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Missing meeting audio results in 404 without invoking transcript processor."""

    class _StubProcessor:
        def __init__(self) -> None:
            self.calls: list[Path] = []

        async def process(self, audio_path: Path) -> NoReturn:
            self.calls.append(audio_path)
            message = 'process should not be called for missing meetings'
            raise AssertionError(message)

    processor = _StubProcessor()
    session = cast('AsyncSession', MagicMock(spec=AsyncSession))
    service = TranscriptService(
        session,
        cast('MeetingProcessingService', processor),
        raw_audio_dir=tmp_path,
    )
    client = TestClient(fastapi_app)
    headers, user = await _build_auth_headers(fastapi_db_session)
    repository = MeetingRepository(fastapi_db_session)
    stored_meeting = await repository.create(user_id=user.id, filename='audio.wav')
    await fastapi_db_session.commit()
    meeting_id = str(stored_meeting.id)
    overrides: OverrideMap = {get_transcript_service: lambda: service}
    with _override_dependencies(fastapi_app, overrides):
        response = client.get(f'/api/meeting/{meeting_id}/stream', headers=headers)

    assert response.status_code == HTTPStatus.NOT_FOUND, response.json()
    assert response.json() == {'detail': f'Meeting {meeting_id} not found'}
    assert processor.calls == []


@pytest.mark.asyncio
async def test_stream_emits_heartbeat_before_payload(
    monkeypatch: pytest.MonkeyPatch,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """SSE stream sends heartbeat comments while awaiting payloads."""

    class _DelayedService:
        def __init__(self) -> None:
            self.checked: list[str] = []
            self.streamed: list[str] = []

        def ensure_audio_available(self, meeting_id: str) -> None:
            self.checked.append(meeting_id)

        def stream_transcript(self, meeting_id: str) -> AsyncGenerator[dict[str, object], None]:
            self.streamed.append(meeting_id)

            async def generator() -> AsyncGenerator[dict[str, object], None]:
                await asyncio.sleep(0.03)
                yield {'event': 'summary', 'data': {'summary': 'Done'}}

            return generator()

    service = _DelayedService()
    client = TestClient(fastapi_app)
    headers, user = await _build_auth_headers(fastapi_db_session)
    repository = MeetingRepository(fastapi_db_session)
    stored_meeting = await repository.create(user_id=user.id, filename='audio.wav')
    await fastapi_db_session.commit()
    meeting_id = str(stored_meeting.id)
    overrides: OverrideMap = {get_transcript_service: lambda: service}
    monkeypatch.setattr(meeting, 'HEARTBEAT_INTERVAL_SECONDS', 0.01)
    monkeypatch.setattr(meeting, 'STREAM_IDLE_TIMEOUT_SECONDS', 0.2)

    lines: list[str] = []
    with (
        _override_dependencies(fastapi_app, overrides),
        client.stream('GET', f'/api/meeting/{meeting_id}/stream', headers=headers) as response,
    ):
        assert response.status_code == HTTPStatus.OK, response.status_code
        lines = [line for line in response.iter_lines() if line]

    assert ': heartbeat' in lines
    assert lines[-2:] == [
        'event: summary',
        'data: {"summary": "Done"}',
    ]
    assert service.checked == [meeting_id]


@pytest.mark.asyncio
async def test_stream_stops_after_idle_timeout(
    monkeypatch: pytest.MonkeyPatch,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Stream closes when payloads are not produced within idle timeout."""

    class _HangingService:
        def __init__(self) -> None:
            self.stream_requests: list[str] = []

        def ensure_audio_available(self, meeting_id: str) -> None:
            del meeting_id

        def stream_transcript(self, meeting_id: str) -> AsyncGenerator[dict[str, object], None]:
            self.stream_requests.append(meeting_id)

            async def generator() -> AsyncGenerator[dict[str, object], None]:
                await asyncio.sleep(1)
                yield {'event': 'summary', 'data': {'summary': 'Late'}}

            return generator()

    service = _HangingService()
    client = TestClient(fastapi_app)
    headers, user = await _build_auth_headers(fastapi_db_session)
    repository = MeetingRepository(fastapi_db_session)
    stored_meeting = await repository.create(user_id=user.id, filename='audio.wav')
    await fastapi_db_session.commit()
    meeting_id = str(stored_meeting.id)
    overrides: OverrideMap = {get_transcript_service: lambda: service}
    monkeypatch.setattr(meeting, 'HEARTBEAT_INTERVAL_SECONDS', 0.01)
    monkeypatch.setattr(meeting, 'STREAM_IDLE_TIMEOUT_SECONDS', 0.05)

    lines: list[str] = []
    with (
        _override_dependencies(fastapi_app, overrides),
        client.stream('GET', f'/api/meeting/{meeting_id}/stream', headers=headers) as response,
    ):
        assert response.status_code == HTTPStatus.OK, response.status_code
        lines = [line for line in response.iter_lines() if line]

    assert lines
    assert all(line == ': heartbeat' for line in lines)


@pytest.mark.asyncio
async def test_upload_and_stream_persists_transcripts(
    tmp_path: Path,
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """End-to-end flow stores transcripts and marks the meeting completed."""
    events: list[MeetingEvent] = [
        {
            'speaker': 'A',
            'text': 'Hello',
            'confidence': 0.93,
            'summary_fragment': 'Greeting',
            'start': 0.0,
        },
        {
            'speaker': 'B',
            'text': 'World',
            'confidence': 0.88,
            'summary_fragment': 'Response',
            'start': 2.5,
        },
    ]
    result = MeetingProcessingResult(events=events, summary='Session summary')
    processor = _RecordingProcessor(result)

    raw_audio_dir = tmp_path / 'audio'
    raw_audio_dir.mkdir()

    client = TestClient(fastapi_app)
    headers, _ = await _build_auth_headers(fastapi_db_session)

    meeting_id = ''
    payload_lines: list[str] = []
    async with _override_transcript_dependencies(fastapi_app, raw_audio_dir, processor):
        upload_response = client.post(
            '/api/meeting/upload',
            files={'file': ('audio.wav', b'hello world', 'audio/wav')},
            headers=headers,
        )

        assert upload_response.status_code == HTTPStatus.OK, upload_response.json()
        meeting_id = upload_response.json()['meeting_id']

        with client.stream(
            'GET', f'/api/meeting/{meeting_id}/stream', headers=headers
        ) as stream_response:
            assert stream_response.status_code == HTTPStatus.OK, stream_response.status_code
            payload_lines = [line for line in stream_response.iter_lines() if line]

    audio_path = raw_audio_dir / f'{meeting_id}.wav'
    assert processor.calls == [audio_path]

    assert payload_lines
    assert len(payload_lines) % 2 == 0
    events_streamed: list[tuple[str, dict[str, object]]] = []
    for index in range(0, len(payload_lines), 2):
        event_line = payload_lines[index]
        data_line = payload_lines[index + 1]
        assert event_line.startswith('event: ')
        assert data_line.startswith('data: ')
        event_type = event_line.split(': ', 1)[1]
        data = json.loads(data_line.split(': ', 1)[1])
        events_streamed.append((event_type, data))

    assert events_streamed == [
        ('transcript', events[0]),
        ('transcript', events[1]),
        ('summary', {'summary': 'Session summary'}),
    ]

    meeting_repository = MeetingRepository(fastapi_db_session)
    stored_meeting = await meeting_repository.get_by_id(UUID(meeting_id))
    assert stored_meeting is not None
    assert stored_meeting.status == MeetingStatus.COMPLETED
    assert stored_meeting.summary == 'Session summary'

    transcript_repository = TranscriptRepository(fastapi_db_session)
    transcripts = await transcript_repository.list_by_meeting(UUID(meeting_id))
    assert [fragment.text for fragment in transcripts] == ['Hello', 'World']
    assert [fragment.speaker_id for fragment in transcripts] == ['A', 'B']
    assert transcripts[0].timestamp is not None
    assert transcripts[0].timestamp < transcripts[1].timestamp


@pytest.mark.asyncio
async def test_stream_forbidden_for_other_user(
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Streaming transcript for another user's meeting returns 403."""
    _, owner = await _build_auth_headers(fastapi_db_session)
    repository = MeetingRepository(fastapi_db_session)
    stored_meeting = await repository.create(user_id=owner.id, filename='audio.wav')
    await fastapi_db_session.commit()
    meeting_id = str(stored_meeting.id)

    headers_other, _ = await _build_auth_headers(fastapi_db_session)

    client = TestClient(fastapi_app)
    response = client.get(f'/api/meeting/{meeting_id}/stream', headers=headers_other)
    assert response.status_code == HTTPStatus.FORBIDDEN, response.json()
    assert response.json() == {'detail': 'You do not have access to this meeting'}


@pytest.mark.asyncio
async def test_get_meeting_details_returns_transcripts(
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Meeting detail endpoint returns stored transcript segments."""
    headers, user = await _build_auth_headers(fastapi_db_session)
    meeting_repository = MeetingRepository(fastapi_db_session)
    meeting = await meeting_repository.create(
        user_id=user.id,
        filename='session.wav',
        status=MeetingStatus.COMPLETED,
    )
    meeting = await meeting_repository.update(meeting, summary='Summary text')

    transcript_repository = TranscriptRepository(fastapi_db_session)
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    first = await transcript_repository.create(
        meeting_id=meeting.id,
        text='Hello there',
        speaker_id='speaker-1',
        timestamp=timestamp,
    )
    second = await transcript_repository.create(
        meeting_id=meeting.id,
        text='General Kenobi',
        speaker_id='speaker-2',
        timestamp=timestamp + timedelta(seconds=5),
    )
    await fastapi_db_session.commit()

    client = TestClient(fastapi_app)
    response = client.get(f'/api/meeting/{meeting.id}', headers=headers)
    assert response.status_code == HTTPStatus.OK, response.json()
    payload = response.json()

    assert payload['id'] == str(meeting.id)
    assert payload['filename'] == 'session.wav'
    assert payload['status'] == MeetingStatus.COMPLETED.value
    assert payload['summary'] == 'Summary text'
    assert payload['created_at'] == meeting.created_at.isoformat()
    transcripts = payload['transcripts']
    expected_transcript_count = 2
    assert len(transcripts) == expected_transcript_count

    first_payload = transcripts[0]
    assert first_payload['id'] == str(first.id)
    assert first_payload['text'] == 'Hello there'
    assert first_payload['speaker_id'] == 'speaker-1'
    assert datetime.fromisoformat(first_payload['timestamp'].replace('Z', '+00:00')) == timestamp

    second_payload = transcripts[1]
    assert second_payload['id'] == str(second.id)
    assert second_payload['text'] == 'General Kenobi'
    assert second_payload['speaker_id'] == 'speaker-2'
    expected_second_timestamp = timestamp + timedelta(seconds=5)
    second_timestamp = second_payload['timestamp'].replace('Z', '+00:00')
    assert datetime.fromisoformat(second_timestamp) == expected_second_timestamp


@pytest.mark.asyncio
async def test_get_meeting_details_requires_completed_status(
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Meeting detail endpoint rejects non-completed meetings."""
    headers, user = await _build_auth_headers(fastapi_db_session)
    meeting_repository = MeetingRepository(fastapi_db_session)
    meeting = await meeting_repository.create(
        user_id=user.id,
        filename='session.wav',
        status=MeetingStatus.PROCESSING,
    )
    await fastapi_db_session.commit()

    client = TestClient(fastapi_app)
    response = client.get(f'/api/meeting/{meeting.id}', headers=headers)
    assert response.status_code == HTTPStatus.CONFLICT, response.json()
    assert response.json() == {'detail': 'Transcript is not available yet.'}


@pytest.mark.asyncio
async def test_get_meeting_details_forbidden_for_other_user(
    fastapi_app: 'FastAPI',
    fastapi_db_session: AsyncSession,
) -> None:
    """Users cannot fetch transcripts belonging to another account."""
    _, owner = await _build_auth_headers(fastapi_db_session)
    meeting_repository = MeetingRepository(fastapi_db_session)
    meeting = await meeting_repository.create(
        user_id=owner.id,
        filename='session.wav',
        status=MeetingStatus.COMPLETED,
    )
    await fastapi_db_session.commit()

    headers_other, _ = await _build_auth_headers(fastapi_db_session)

    client = TestClient(fastapi_app)
    response = client.get(f'/api/meeting/{meeting.id}', headers=headers_other)
    assert response.status_code == HTTPStatus.FORBIDDEN, response.json()
    assert response.json() == {'detail': 'You do not have access to this meeting'}
