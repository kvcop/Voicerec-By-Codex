"""Tests for meeting API endpoints."""

import asyncio
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import contextmanager
from http import HTTPStatus
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, NoReturn, Self, cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import meeting
from app.core.security import create_access_token, hash_password
from app.core.settings import DEFAULT_RAW_AUDIO_DIR, get_settings
from app.db.repositories import MeetingRepository
from app.db.repositories.user import UserRepository
from app.services.auth import AUTH_SCHEME_BEARER
from app.services.transcript import (
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


@contextmanager
def _override_dependencies(app: 'FastAPI', overrides: OverrideMap) -> Iterator[None]:
    """Temporarily apply dependency overrides for the FastAPI app."""
    app.dependency_overrides.update(overrides)
    try:
        yield
    finally:
        for dependency in overrides:
            app.dependency_overrides.pop(dependency, None)


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
