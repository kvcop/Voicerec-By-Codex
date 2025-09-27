"""Tests for meeting API endpoints."""

import asyncio
from collections.abc import AsyncGenerator
from http import HTTPStatus
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, NoReturn, Self, cast
from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import meeting
from app.core.settings import DEFAULT_RAW_AUDIO_DIR, get_settings
from app.main import app
from app.services.transcript import (
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
)

if TYPE_CHECKING:  # pragma: no cover - imports for type hints
    from app.services.meeting_processing import MeetingProcessingService

client = TestClient(app)


def test_raw_audio_dir_default_location(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default raw audio storage path resides under repository data/raw."""
    monkeypatch.delenv('RAW_AUDIO_DIR', raising=False)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://example')
    monkeypatch.setenv('GPU_GRPC_HOST', 'host')
    monkeypatch.setenv('GPU_GRPC_PORT', '1234')

    get_settings.cache_clear()
    raw_dir = resolve_raw_audio_dir()
    try:
        assert raw_dir == DEFAULT_RAW_AUDIO_DIR
        assert 'backend' not in raw_dir.parts
        assert raw_dir.is_dir()
    finally:
        get_settings.cache_clear()


def test_upload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Uploading audio saves file and returns meeting id."""
    meeting_id = 'abc123'

    class _UUID:
        hex = meeting_id

    monkeypatch.setattr(meeting, 'uuid4', lambda: _UUID())
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

    app.dependency_overrides[meeting.get_raw_audio_dir] = lambda: tmp_path
    try:
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('audio.wav', data, 'audio/wav')},
        )
    finally:
        app.dependency_overrides.pop(meeting.get_raw_audio_dir, None)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'meeting_id': meeting_id}
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == data
    assert opened_files
    assert opened_files[0].closed is True


def test_upload_rejects_non_wav(tmp_path: Path) -> None:
    """Uploading non-WAV files is rejected with 415 status."""
    app.dependency_overrides[meeting.get_raw_audio_dir] = lambda: tmp_path
    try:
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('notes.txt', b'123', 'text/plain')},
        )
    finally:
        app.dependency_overrides.pop(meeting.get_raw_audio_dir, None)

    assert response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert response.json() == {'detail': 'Only WAV audio is supported.'}
    assert not list(tmp_path.iterdir())


def test_upload_accepts_mixed_case_mime(tmp_path: Path) -> None:
    """Mixed-case WAV MIME types are accepted."""
    app.dependency_overrides[meeting.get_raw_audio_dir] = lambda: tmp_path
    try:
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('audio.wav', b'abc', 'audio/WAV')},
        )
    finally:
        app.dependency_overrides.pop(meeting.get_raw_audio_dir, None)

    assert response.status_code == HTTPStatus.OK
    assert 'meeting_id' in response.json()
    assert list(tmp_path.iterdir())


def test_upload_streams_large_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Large uploads are streamed to disk without buffering entire payload."""
    meeting_id = 'big'

    class _UUID:
        hex = meeting_id

    monkeypatch.setattr(meeting, 'uuid4', lambda: _UUID())
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

    app.dependency_overrides[meeting.get_raw_audio_dir] = lambda: tmp_path
    try:
        response = client.post(
            '/api/meeting/upload',
            files={'file': ('audio.wav', b'dummy', 'audio/wav')},
        )
    finally:
        app.dependency_overrides.pop(meeting.get_raw_audio_dir, None)

    assert response.status_code == HTTPStatus.OK
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == b''.join(chunks)
    assert writes == chunks


def test_stream() -> None:
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
    app.dependency_overrides[get_transcript_service] = lambda: fake_service

    lines: list[str] = []
    try:
        with client.stream('GET', '/api/meeting/xyz/stream') as response:
            assert response.status_code == HTTPStatus.OK
            lines = [line for line in response.iter_lines() if line != '']
    finally:
        app.dependency_overrides.pop(get_transcript_service, None)

    assert lines == [
        'event: transcript',
        'data: {"speaker": "A", "text": "hello"}',
        'event: transcript',
        'data: {"speaker": "B", "text": "world"}',
        'event: summary',
        'data: {"summary": "Done"}',
    ]
    assert fake_service.calls == ['xyz']


def test_stream_missing_meeting_returns_404(tmp_path: Path) -> None:
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
    app.dependency_overrides[get_transcript_service] = lambda: service

    try:
        response = client.get('/api/meeting/missing/stream')
    finally:
        app.dependency_overrides.pop(get_transcript_service, None)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Meeting missing not found'}
    assert processor.calls == []


def test_stream_emits_heartbeat_before_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """SSE stream sends heartbeat comments while awaiting payloads."""

    class _DelayedService:
        def __init__(self) -> None:
            self.checked: list[str] = []

        def ensure_audio_available(self, meeting_id: str) -> None:
            self.checked.append(meeting_id)

        def stream_transcript(self, meeting_id: str) -> AsyncGenerator[dict[str, object], None]:
            assert meeting_id == 'meeting-id'

            async def generator() -> AsyncGenerator[dict[str, object], None]:
                await asyncio.sleep(0.03)
                yield {'event': 'summary', 'data': {'summary': 'Done'}}

            return generator()

    service = _DelayedService()
    app.dependency_overrides[get_transcript_service] = lambda: service
    monkeypatch.setattr(meeting, 'HEARTBEAT_INTERVAL_SECONDS', 0.01)
    monkeypatch.setattr(meeting, 'STREAM_IDLE_TIMEOUT_SECONDS', 0.2)

    lines: list[str] = []
    try:
        with client.stream('GET', '/api/meeting/meeting-id/stream') as response:
            assert response.status_code == HTTPStatus.OK
            lines = [line for line in response.iter_lines() if line]
    finally:
        app.dependency_overrides.pop(get_transcript_service, None)

    assert ': heartbeat' in lines
    assert lines[-2:] == [
        'event: summary',
        'data: {"summary": "Done"}',
    ]
    assert service.checked == ['meeting-id']


def test_stream_stops_after_idle_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stream closes when payloads are not produced within idle timeout."""

    class _HangingService:
        def ensure_audio_available(self, meeting_id: str) -> None:
            del meeting_id

        def stream_transcript(self, meeting_id: str) -> AsyncGenerator[dict[str, object], None]:
            assert meeting_id == 'meeting-id'

            async def generator() -> AsyncGenerator[dict[str, object], None]:
                await asyncio.sleep(1)
                yield {'event': 'summary', 'data': {'summary': 'Late'}}

            return generator()

    service = _HangingService()
    app.dependency_overrides[get_transcript_service] = lambda: service
    monkeypatch.setattr(meeting, 'HEARTBEAT_INTERVAL_SECONDS', 0.01)
    monkeypatch.setattr(meeting, 'STREAM_IDLE_TIMEOUT_SECONDS', 0.05)

    lines: list[str] = []
    try:
        with client.stream('GET', '/api/meeting/meeting-id/stream') as response:
            assert response.status_code == HTTPStatus.OK
            lines = [line for line in response.iter_lines() if line]
    finally:
        app.dependency_overrides.pop(get_transcript_service, None)

    assert lines
    assert all(line == ': heartbeat' for line in lines)
