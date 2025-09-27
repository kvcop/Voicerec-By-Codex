"""Transcript database model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._types import GUID, DatetimeType

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class Transcript(Base):
    """Transcribed fragment of a meeting."""

    __tablename__ = 'transcripts'
    __table_args__ = (Index('ix_transcripts_meeting_timestamp', 'meeting_id', 'timestamp'),)

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    meeting_id: Mapped[UUID] = mapped_column(
        ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    speaker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[DatetimeType] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    meeting: Mapped[Meeting] = relationship(back_populates='transcripts')
