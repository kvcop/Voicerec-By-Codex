"""Common helpers for SQLAlchemy repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from app.db.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar('ModelT', bound=Base)


class SQLAlchemyRepository(Generic[ModelT]):
    """Base repository providing access to the async session."""

    def __init__(self, session: AsyncSession) -> None:
        """Store session instance for subclasses."""
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """Return the session associated with the repository."""
        return self._session
