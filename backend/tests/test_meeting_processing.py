"""Tests for meeting processing domain service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

import pytest

from app.services.meeting_processing import MeetingProcessingService


class _StaticClient:
    """Return predefined payload regardless of the input."""

    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.streams: list[bytes] = []
        self.calls: list[str] = []

    async def run(self, argument: Iterable[bytes] | str) -> dict[str, object]:
        if isinstance(argument, str):
            self.calls.append(argument)
        else:
            self.streams.append(b''.join(argument))
        return cast('dict[str, object]', json.loads(json.dumps(self.payload)))


@pytest.fixture
def diarize_payload() -> dict[str, object]:
    """Return diarization payload loaded from fixture."""
    fixture_path = Path(__file__).resolve().parent / 'fixtures' / 'diarize.json'
    return json.loads(fixture_path.read_text(encoding='utf-8'))


@pytest.fixture
def summarize_payload() -> dict[str, object]:
    """Return summarization payload loaded from fixture."""
    fixture_path = Path(__file__).resolve().parent / 'fixtures' / 'summarize.json'
    return json.loads(fixture_path.read_text(encoding='utf-8'))


@pytest.mark.asyncio
async def test_meeting_processing_merges_segments(
    diarize_payload: dict[str, object],
    summarize_payload: dict[str, object],
    tmp_path: Path,
) -> None:
    """Transcription and diarization data are merged into structured events."""
    transcribe_payload = {
        'segments': [
            {'start': 0.0, 'end': 1.0, 'text': ' Hello ', 'confidence': 0.95},
            {'start': 1.0, 'end': 2.0, 'text': 'World', 'confidence': 0.75},
        ]
    }

    transcribe_client = _StaticClient(transcribe_payload)
    diarize_client = _StaticClient(diarize_payload)
    summarize_client = _StaticClient(summarize_payload)

    service = MeetingProcessingService(transcribe_client, diarize_client, summarize_client)

    audio_path = tmp_path / 'audio.wav'
    audio_path.write_bytes(b'hello world')
    result = await service.process(audio_path)

    assert transcribe_client.streams == [b'hello world']
    assert diarize_client.streams == [b'hello world']
    assert summarize_client.calls == ['Hello World']

    assert result.summary == 'This is a summary.'
    assert result.events == [
        {
            'speaker': 'A',
            'text': 'Hello',
            'confidence': pytest.approx(0.95),
            'summary_fragment': 'This is a summary.',
        },
        {
            'speaker': 'B',
            'text': 'World',
            'confidence': pytest.approx(0.75),
            'summary_fragment': '',
        },
    ]
