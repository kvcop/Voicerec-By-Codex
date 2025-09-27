"""Repository for ``User`` ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.repositories.base import SQLAlchemyRepository
from app.models.user import User

if TYPE_CHECKING:
    from uuid import UUID


class UserRepository(SQLAlchemyRepository[User]):
    """Perform CRUD operations for :class:`~app.models.user.User`."""

    async def create(self, *, email: str, hashed_password: str) -> User:
        """Persist a new user and return the created instance."""
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Return user identified by ``user_id`` or ``None`` if absent."""
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Return user with the matching email address if it exists."""
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(self) -> list[User]:
        """Return all users ordered by creation timestamp."""
        statement = select(User).order_by(User.created_at)
        result = await self.session.execute(statement)
        return list(result.scalars())

    async def update(
        self,
        user: User,
        *,
        email: str | None = None,
        hashed_password: str | None = None,
    ) -> User:
        """Update provided ``user`` instance with supplied fields."""
        if email is not None:
            user.email = email
        if hashed_password is not None:
            user.hashed_password = hashed_password
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Remove ``user`` from the database."""
        await self.session.delete(user)
        await self.session.flush()
