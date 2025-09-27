"""Meeting database model."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._types import GUID, DatetimeType

if TYPE_CHECKING:
    from app.models.transcript import Transcript
    from app.models.user import User


class MeetingStatus(StrEnum):
    """Possible statuses for a meeting transcription workflow."""

    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class Meeting(Base):
    """Recorded meeting stored in the database."""

    __tablename__ = 'meetings'
    __table_args__ = (Index('ix_meetings_user_created_at', 'user_id', 'created_at'),)

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[DatetimeType] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus, name='meeting_status', native_enum=False),
        default=MeetingStatus.PENDING,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates='meetings')
    transcripts: Mapped[list[Transcript]] = relationship(
        back_populates='meeting', cascade='all, delete-orphan'
    )
