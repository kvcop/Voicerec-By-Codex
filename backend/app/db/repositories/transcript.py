"""Repository for ``Transcript`` ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.repositories.base import SQLAlchemyRepository
from app.models.transcript import Transcript

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class TranscriptRepository(SQLAlchemyRepository[Transcript]):
    """Perform CRUD operations for :class:`~app.models.transcript.Transcript`."""

    async def create(
        self,
        *,
        meeting_id: UUID,
        text: str,
        speaker_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> Transcript:
        """Persist a new transcript entry."""
        transcript = Transcript(meeting_id=meeting_id, text=text, speaker_id=speaker_id)
        if timestamp is not None:
            transcript.timestamp = timestamp
        self.session.add(transcript)
        await self.session.flush()
        await self.session.refresh(transcript)
        return transcript

    async def get_by_id(self, transcript_id: UUID) -> Transcript | None:
        """Return transcript identified by ``transcript_id`` if it exists."""
        return await self.session.get(Transcript, transcript_id)

    async def list_by_meeting(self, meeting_id: UUID) -> list[Transcript]:
        """Return transcripts for the provided meeting ordered by timestamp."""
        statement = (
            select(Transcript)
            .where(Transcript.meeting_id == meeting_id)
            .order_by(Transcript.timestamp)
        )
        result = await self.session.execute(statement)
        return list(result.scalars())

    async def update(
        self,
        transcript: Transcript,
        *,
        text: str | None = None,
        speaker_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> Transcript:
        """Update transcript attributes with supplied values."""
        if text is not None:
            transcript.text = text
        if speaker_id is not None:
            transcript.speaker_id = speaker_id
        if timestamp is not None:
            transcript.timestamp = timestamp
        self.session.add(transcript)
        await self.session.flush()
        await self.session.refresh(transcript)
        return transcript

    async def delete(self, transcript: Transcript) -> None:
        """Remove transcript from the database."""
        await self.session.delete(transcript)
        await self.session.flush()
