"""Tests for meeting API routes."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.api import meeting
from app.main import app
from app.services.transcript import get_transcript_service

if TYPE_CHECKING:  # pragma: no cover - imports for type hints
    from collections.abc import AsyncGenerator

    import pytest

client = TestClient(app)


def test_raw_audio_dir_default_location() -> None:
    """Default raw audio storage path resides under repository data/raw."""
    raw_dir = meeting.RAW_AUDIO_DIR
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
    monkeypatch.setattr(meeting, 'RAW_AUDIO_DIR', tmp_path)

    monkeypatch.setattr(meeting, 'CHUNK_SIZE', 1024)

    data = bytes(range(256)) * 4096

    response = client.post('/upload', files={'file': ('audio.wav', data)})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'meeting_id': meeting_id}
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == data


def test_stream() -> None:
    """SSE endpoint streams transcript fragments and sends termination event."""

    class _FakeTranscriptService:
        def __init__(self) -> None:
            self.calls: list[str] = []

        async def stream_transcript(
            self, meeting_id: str
        ) -> AsyncGenerator[dict[str, int | str], None]:
            self.calls.append(meeting_id)
            yield {'index': 1, 'text': 'hello'}
            yield {'index': 2, 'text': 'world'}

    fake_service = _FakeTranscriptService()
    app.dependency_overrides[get_transcript_service] = lambda: fake_service

    lines: list[str] = []
    try:
        with client.stream('GET', '/stream/xyz') as response:
            assert response.status_code == HTTPStatus.OK
            lines = [line for line in response.iter_lines() if line != '']
    finally:
        app.dependency_overrides.pop(get_transcript_service, None)

    assert lines == [
        'data: {"index": 1, "text": "hello"}',
        'data: {"index": 2, "text": "world"}',
        'event: end',
        'data: {}',
    ]
    assert fake_service.calls == ['xyz']
