"""User database model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._types import GUID, DatetimeType

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class User(Base):
    """Persisted application user."""

    __tablename__ = 'users'
    __table_args__ = (UniqueConstraint('email', name='uq_users_email'),)

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[DatetimeType] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DatetimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    meetings: Mapped[list[Meeting]] = relationship(
        back_populates='user', cascade='all, delete-orphan'
    )
