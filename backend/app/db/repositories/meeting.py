"""Repository for ``Meeting`` ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.repositories.base import SQLAlchemyRepository
from app.models.meeting import Meeting, MeetingStatus

if TYPE_CHECKING:
    from uuid import UUID


class MeetingRepository(SQLAlchemyRepository[Meeting]):
    """Perform CRUD operations for :class:`~app.models.meeting.Meeting`."""

    async def create(
        self,
        *,
        user_id: UUID,
        filename: str,
        status: MeetingStatus = MeetingStatus.PENDING,
    ) -> Meeting:
        """Persist a new meeting for the provided user."""
        meeting = Meeting(user_id=user_id, filename=filename, status=status)
        self.session.add(meeting)
        await self.session.flush()
        await self.session.refresh(meeting)
        return meeting

    async def get_by_id(self, meeting_id: UUID) -> Meeting | None:
        """Return meeting identified by ``meeting_id`` if it exists."""
        return await self.session.get(Meeting, meeting_id)

    async def list_by_user(self, user_id: UUID) -> list[Meeting]:
        """Return meetings that belong to the provided user."""
        statement = (
            select(Meeting).where(Meeting.user_id == user_id).order_by(Meeting.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars())

    async def update(
        self,
        meeting: Meeting,
        *,
        filename: str | None = None,
        status: MeetingStatus | None = None,
    ) -> Meeting:
        """Update meeting attributes with provided values."""
        if filename is not None:
            meeting.filename = filename
        if status is not None:
            meeting.status = status
        self.session.add(meeting)
        await self.session.flush()
        await self.session.refresh(meeting)
        return meeting

    async def delete(self, meeting: Meeting) -> None:
        """Remove meeting from the database."""
        await self.session.delete(meeting)
        await self.session.flush()
