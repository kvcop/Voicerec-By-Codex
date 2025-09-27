"""Tests for database repository implementations."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import pytest

from app.db.repositories import MeetingRepository, TranscriptRepository, UserRepository
from app.models.meeting import MeetingStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def _fake_hash(seed: str) -> str:
    """Return deterministic pseudo hash for test credentials."""
    return hashlib.sha256(seed.encode('utf-8')).hexdigest()


@pytest.mark.asyncio
async def test_user_repository_crud(db_session: AsyncSession) -> None:
    """Ensure user repository performs basic CRUD operations."""
    repository = UserRepository(db_session)

    created = await repository.create(email='user@example.com', hashed_password=_fake_hash('user'))
    assert created.id is not None

    fetched = await repository.get_by_id(created.id)
    assert fetched is created

    by_email = await repository.get_by_email('user@example.com')
    assert by_email is created

    updated = await repository.update(created, hashed_password=_fake_hash('updated'))
    assert updated.hashed_password == _fake_hash('updated')

    users = await repository.list()
    assert [user.id for user in users] == [created.id]

    await repository.delete(created)
    assert await repository.get_by_id(created.id) is None


@pytest.mark.asyncio
async def test_meeting_repository_filters_by_user(db_session: AsyncSession) -> None:
    """Meeting repository should filter meetings by owning user."""
    user_repository = UserRepository(db_session)
    meeting_repository = MeetingRepository(db_session)

    owner = await user_repository.create(
        email='owner@example.com',
        hashed_password=_fake_hash('owner'),
    )
    other_user = await user_repository.create(
        email='other@example.com',
        hashed_password=_fake_hash('other'),
    )

    meeting_one = await meeting_repository.create(user_id=owner.id, filename='one.wav')
    meeting_two = await meeting_repository.create(
        user_id=owner.id,
        filename='two.wav',
        status=MeetingStatus.PROCESSING,
    )
    await meeting_repository.create(user_id=other_user.id, filename='ignored.wav')

    meetings = await meeting_repository.list_by_user(owner.id)
    assert [meeting.id for meeting in meetings] == [meeting_two.id, meeting_one.id]

    fetched = await meeting_repository.get_by_id(meeting_one.id)
    assert fetched is meeting_one

    updated = await meeting_repository.update(meeting_one, status=MeetingStatus.COMPLETED)
    assert updated.status is MeetingStatus.COMPLETED

    await meeting_repository.delete(meeting_two)
    assert await meeting_repository.get_by_id(meeting_two.id) is None


@pytest.mark.asyncio
async def test_transcript_repository_crud(db_session: AsyncSession) -> None:
    """Transcript repository should manage transcripts for a meeting."""
    user_repository = UserRepository(db_session)
    meeting_repository = MeetingRepository(db_session)
    transcript_repository = TranscriptRepository(db_session)

    owner = await user_repository.create(
        email='speaker@example.com',
        hashed_password=_fake_hash('speaker'),
    )
    meeting = await meeting_repository.create(user_id=owner.id, filename='meeting.wav')

    transcript = await transcript_repository.create(meeting_id=meeting.id, text='Hello world')
    assert transcript.id is not None

    fetched = await transcript_repository.get_by_id(transcript.id)
    assert fetched is transcript

    updated = await transcript_repository.update(
        transcript,
        text='Updated text',
        speaker_id='speaker-1',
    )
    assert updated.text == 'Updated text'
    assert updated.speaker_id == 'speaker-1'

    transcripts = await transcript_repository.list_by_meeting(meeting.id)
    assert [item.id for item in transcripts] == [transcript.id]

    await transcript_repository.delete(transcript)
    assert await transcript_repository.get_by_id(transcript.id) is None
