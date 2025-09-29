"""Authentication-related services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends

from app.core.security import hash_password
from app.db.repositories.user import UserRepository
from app.db.session import get_session

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User


class EmailAlreadyExistsError(Exception):
    """Raised when attempting to register an already registered email address."""

    def __init__(self, email: str) -> None:
        message = f'User with email {email} already exists'
        super().__init__(message)
        self.email = email


class AuthService:
    """Application service handling authentication flows."""

    def __init__(self, session: AsyncSession) -> None:
        """Store dependencies required for authentication operations."""
        self._session = session
        self._user_repository = UserRepository(session)

    async def register_user(self, *, email: str, password: str) -> User:
        """Create a new user account with the provided credentials."""
        existing_user = await self._user_repository.get_by_email(email)
        if existing_user is not None:
            raise EmailAlreadyExistsError(email)

        hashed = hash_password(password)
        user = await self._user_repository.create(email=email, hashed_password=hashed)
        await self._session.commit()
        return user


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    """Return ``AuthService`` instance wired with the database session dependency."""
    return AuthService(session)
