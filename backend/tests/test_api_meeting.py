"""Tests for meeting API routes."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.api import meeting
from app.main import app

if TYPE_CHECKING:  # pragma: no cover - imports for type hints
    from collections.abc import AsyncGenerator

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

    response = client.post('/upload', files={'file': ('audio.wav', b'data')})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'meeting_id': meeting_id}
    saved = tmp_path / f'{meeting_id}.wav'
    assert saved.read_bytes() == b'data'


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
