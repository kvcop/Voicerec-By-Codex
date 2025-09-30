"""Unit tests for the transcript service."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from app.db.repositories import MeetingRepository, TranscriptRepository, UserRepository
from app.models.meeting import MeetingStatus
from app.services.meeting_processing import MeetingEvent, MeetingProcessingResult
from app.services.transcript import MeetingNotFoundError, TranscriptService

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.services.meeting_processing import MeetingProcessingService


DUMMY_USER_HASH = 'dummy-user-hash'


class _StubProcessor:
    """Return a preconfigured meeting processing result."""

    def __init__(self, result: MeetingProcessingResult) -> None:
        self.result = result
        self.calls: list[Path] = []

    async def process(self, audio_path: Path) -> MeetingProcessingResult:
        self.calls.append(audio_path)
        return self.result


@pytest.mark.asyncio
async def test_stream_transcript_persists_results(tmp_path: Path, db_session: AsyncSession) -> None:
    """Service persists transcript fragments and updates meeting status."""
    audio_dir = tmp_path / 'audio'
    audio_dir.mkdir()

    user_repository = UserRepository(db_session)
    user = await user_repository.create(email='user@example.com', hashed_password=DUMMY_USER_HASH)
    meeting_repository = MeetingRepository(db_session)
    meeting = await meeting_repository.create(user_id=user.id, filename='audio.wav')
    await db_session.commit()

    meeting_id = str(meeting.id)
    audio_path = audio_dir / f'{meeting_id}.wav'
    audio_path.write_bytes(b'dummy')

    events: list[MeetingEvent] = [
        {
            'speaker': 'A',
            'text': 'Hello there',
            'confidence': 0.9,
            'summary_fragment': 'Greeting',
            'start': 0.0,
        },
        {
            'speaker': 'B',
            'text': 'Hi!',
            'confidence': 0.8,
            'summary_fragment': 'Response',
            'start': 5.0,
        },
    ]
    result = MeetingProcessingResult(events=events, summary='Conversation summary')
    processor = _StubProcessor(result)
    service = TranscriptService(
        db_session,
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

    transcript_repository = TranscriptRepository(db_session)
    stored_transcripts = await transcript_repository.list_by_meeting(meeting.id)
    assert [fragment.text for fragment in stored_transcripts] == ['Hello there', 'Hi!']
    assert [fragment.speaker_id for fragment in stored_transcripts] == ['A', 'B']
    assert stored_transcripts[0].timestamp <= stored_transcripts[1].timestamp

    refreshed_meeting = await meeting_repository.get_by_id(meeting.id)
    assert refreshed_meeting is not None
    assert refreshed_meeting.status == MeetingStatus.COMPLETED
    assert refreshed_meeting.summary == 'Conversation summary'


def test_ensure_audio_available_raises_for_missing_file(tmp_path: Path) -> None:
    """Service raises ``MeetingNotFoundError`` when audio file is absent."""
    processor = _StubProcessor(MeetingProcessingResult(events=[], summary=''))
    service = TranscriptService(
        cast('AsyncSession', object()),
        cast('MeetingProcessingService', processor),
        raw_audio_dir=tmp_path,
    )

    with pytest.raises(MeetingNotFoundError):
        service.ensure_audio_available('missing')

    assert processor.calls == []


class _FailingProcessor:
    """Raise an exception to emulate processing failures."""

    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    async def process(self, audio_path: Path) -> MeetingProcessingResult:
        del audio_path
        raise self.exc


@pytest.mark.asyncio
async def test_stream_transcript_marks_meeting_failed(
    tmp_path: Path, db_session: AsyncSession
) -> None:
    """Meeting status becomes failed when processing raises an exception."""
    audio_dir = tmp_path / 'audio'
    audio_dir.mkdir()

    user_repository = UserRepository(db_session)
    user = await user_repository.create(email='user@example.com', hashed_password=DUMMY_USER_HASH)
    meeting_repository = MeetingRepository(db_session)
    meeting = await meeting_repository.create(user_id=user.id, filename='audio.wav')
    await db_session.commit()

    meeting_id = str(meeting.id)
    audio_path = audio_dir / f'{meeting_id}.wav'
    audio_path.write_bytes(b'dummy')

    processor = _FailingProcessor(RuntimeError('processing failed'))
    service = TranscriptService(
        db_session,
        cast('MeetingProcessingService', processor),
        raw_audio_dir=audio_dir,
    )

    stream = service.stream_transcript(meeting_id)
    iterator = aiter(stream)

    with pytest.raises(RuntimeError, match='processing failed'):
        await anext(iterator)

    refreshed_meeting = await meeting_repository.get_by_id(meeting.id)
    assert refreshed_meeting is not None
    assert refreshed_meeting.status == MeetingStatus.FAILED
    assert refreshed_meeting.summary is None

    transcript_repository = TranscriptRepository(db_session)
    transcripts = await transcript_repository.list_by_meeting(meeting.id)
    assert transcripts == []
