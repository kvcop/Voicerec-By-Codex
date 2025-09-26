"""Tests for meeting API routes."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.api import meeting
from app.main import app
from app.services import (
    TranscribeClientProtocol,
    TranscriptRepositoryProtocol,
    TranscriptService,
    get_transcript_service,
)

if TYPE_CHECKING:  # pragma: no cover - imports for type hints
    from collections.abc import AsyncGenerator
    from pathlib import Path

    import pytest

client = TestClient(app)


def test_upload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Uploading audio saves file and returns meeting id."""
    meeting_id = 'abc123'

    class _UUID:
        hex = meeting_id

    monkeypatch.setattr(meeting, 'uuid4', lambda: _UUID())
    monkeypatch.setattr(meeting, 'RAW_DATA_DIR', tmp_path)

    response = client.post('/upload', files={'file': ('audio.wav', b'data')})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'meeting_id': meeting_id}
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == b'data'


async def _fake_stream(_: str) -> AsyncGenerator[str, None]:
    yield 'hello'
    yield 'world'


class _FakeTranscriptRepository(TranscriptRepositoryProtocol):
    async def save_fragment(  # pragma: no cover - stub
        self, _meeting_id: str, _text: str
    ) -> None:
        del _meeting_id, _text


class _FakeTranscribeClient(TranscribeClientProtocol):
    async def run(self, audio_path: Path) -> dict[str, str]:  # pragma: no cover - stub
        return {'audio_path': str(audio_path)}


class _FakeTranscriptService(TranscriptService):
    def __init__(self) -> None:  # pragma: no cover - simple stub
        super().__init__(_FakeTranscriptRepository(), _FakeTranscribeClient())

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[str, None]:
        async for fragment in _fake_stream(meeting_id):
            yield fragment


def test_stream() -> None:
    """SSE endpoint streams transcript fragments."""
    app.dependency_overrides[get_transcript_service] = lambda: _FakeTranscriptService()

    try:
        with client.stream('GET', '/stream/xyz') as response:
            lines = [line for line in response.iter_lines() if line]

        assert lines == ['data: hello', 'data: world']
    finally:
        app.dependency_overrides.pop(get_transcript_service, None)
