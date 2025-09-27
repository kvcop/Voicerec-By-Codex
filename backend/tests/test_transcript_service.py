"""Unit tests for the transcript service."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from app.services.meeting_processing import MeetingEvent, MeetingProcessingResult
from app.services.transcript import MeetingNotFoundError, TranscriptService

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from pathlib import Path

    from app.services.meeting_processing import MeetingProcessingService


class _StubProcessor:
    """Return a preconfigured meeting processing result."""

    def __init__(self, result: MeetingProcessingResult) -> None:
        self.result = result
        self.calls: list[Path] = []

    async def process(self, audio_path: Path) -> MeetingProcessingResult:
        self.calls.append(audio_path)
        return self.result


@pytest.mark.asyncio
async def test_stream_transcript_yields_events(tmp_path: Path) -> None:
    """Service streams transcript events followed by a summary payload."""
    meeting_id = 'meeting123'
    audio_dir = tmp_path / 'audio'
    audio_dir.mkdir()
    audio_path = audio_dir / f'{meeting_id}.wav'
    audio_path.write_bytes(b'dummy')

    events: list[MeetingEvent] = [
        {'speaker': 'A', 'text': 'Hello there', 'confidence': 0.9, 'summary_fragment': 'Greeting'},
        {'speaker': 'B', 'text': 'Hi!', 'confidence': 0.8, 'summary_fragment': 'Response'},
    ]
    result = MeetingProcessingResult(events=events, summary='Conversation summary')
    processor = _StubProcessor(result)
    service = TranscriptService(
        cast('MeetingProcessingService', processor),
        raw_audio_dir=audio_dir,
    )

    stream = [item async for item in service.stream_transcript(meeting_id)]

    assert processor.calls == [audio_path]
    assert stream == [
        {'event': 'transcript', 'data': events[0]},
        {'event': 'transcript', 'data': events[1]},
        {'event': 'summary', 'data': {'summary': 'Conversation summary'}},
    ]


def test_ensure_audio_available_raises_for_missing_file(tmp_path: Path) -> None:
    """Service raises ``MeetingNotFoundError`` when audio file is absent."""
    processor = _StubProcessor(MeetingProcessingResult(events=[], summary=''))
    service = TranscriptService(
        cast('MeetingProcessingService', processor),
        raw_audio_dir=tmp_path,
    )

    with pytest.raises(MeetingNotFoundError):
        service.ensure_audio_available('missing')

    assert processor.calls == []
