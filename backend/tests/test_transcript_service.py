"""Tests for the transcript service audio streaming."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.services.transcript import TranscriptService

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from collections.abc import Iterable
    from pathlib import Path


class _FakeTranscriptClient:
    """Collect audio chunks and return a fixed payload."""

    def __init__(self) -> None:
        self.received: list[bytes] = []

    async def run(self, source: Iterable[bytes]) -> dict[str, str]:
        for chunk in source:
            self.received.append(chunk)
        return {'text': 'hello world from test'}


@pytest.mark.asyncio
async def test_stream_transcript_reads_audio(tmp_path: Path) -> None:
    """Service reads audio file and forwards its chunks to the client."""
    meeting_id = 'meeting123'
    audio_dir = tmp_path / 'audio'
    audio_dir.mkdir()
    audio_path = audio_dir / f'{meeting_id}.wav'
    audio_path.write_bytes(b'hello world')

    client = _FakeTranscriptClient()
    service = TranscriptService(
        client,
        raw_audio_dir=audio_dir,
        words_per_chunk=2,
        audio_chunk_size=4,
    )

    chunks = [chunk async for chunk in service.stream_transcript(meeting_id)]

    assert client.received == [b'hell', b'o wo', b'rld']
    assert chunks == [
        {'index': 1, 'text': 'hello world'},
        {'index': 2, 'text': 'from test'},
    ]
