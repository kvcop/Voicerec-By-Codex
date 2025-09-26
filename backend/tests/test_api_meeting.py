"""Tests for meeting API routes."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Self

from fastapi.testclient import TestClient

from app.api import meeting
from app.main import app

if TYPE_CHECKING:  # pragma: no cover - imports for type hints
    from collections.abc import AsyncGenerator
    from types import TracebackType

    import pytest

client = TestClient(app)


def test_raw_data_dir_default_location() -> None:
    """Default storage path resides under repository data/raw."""
    raw_dir = meeting.RAW_DATA_DIR
    repo_root = Path(__file__).resolve().parents[2]
    assert raw_dir == repo_root / 'data' / 'raw'
    assert 'backend' not in raw_dir.parts
    assert raw_dir.is_dir()


def test_upload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Uploading audio saves file and returns meeting id."""
    meeting_id = 'abc123'

    class _UUID:
        hex = meeting_id

    monkeypatch.setattr(meeting, 'uuid4', lambda: _UUID())
    monkeypatch.setattr(meeting, 'RAW_DATA_DIR', tmp_path)

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

    def _fake_open(path: Path, mode: str = 'r', *_args: object, **_kwargs: object) -> _AsyncFile:
        assert mode == 'wb'
        assert not _args
        assert not _kwargs
        async_file = _AsyncFile(Path(path))
        opened_files.append(async_file)
        return async_file

    monkeypatch.setattr(meeting.aiofiles, 'open', _fake_open)

    response = client.post('/upload', files={'file': ('audio.wav', data)})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'meeting_id': meeting_id}
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == data
    assert opened_files
    assert opened_files[0].closed is True


async def _fake_stream(_: str) -> AsyncGenerator[str, None]:
    yield 'hello'
    yield 'world'


def test_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """SSE endpoint streams transcript fragments."""
    monkeypatch.setattr(
        meeting.TranscriptService,
        'stream_transcript',
        lambda _, meeting_id: _fake_stream(meeting_id),
    )

    with client.stream('GET', '/stream/xyz') as response:
        lines = [line for line in response.iter_lines() if line]
    assert lines == ['data: hello', 'data: world']
