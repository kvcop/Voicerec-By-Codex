"""Authentication-related FastAPI dependencies."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.settings import get_settings
from app.db.repositories.user import UserRepository
from app.db.session import get_session
from app.services.auth import AUTH_SCHEME_BEARER

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User
else:
    AsyncSession = Any
    User = Any


_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Return the authenticated user extracted from the request token."""
    if credentials is None or credentials.scheme.lower() != AUTH_SCHEME_BEARER:
        raise _unauthorized()

    settings = get_settings()
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_token_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        detail = 'Token has expired'
        raise _unauthorized(detail) from exc
    except jwt.InvalidTokenError as exc:
        raise _unauthorized() from exc

    subject = payload.get('sub')
    if subject is None:
        raise _unauthorized()

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise _unauthorized() from exc

    repository = UserRepository(session)
    user = await repository.get_by_id(user_id)
    if user is None:
        detail = 'User account is not permitted to access this resource'
        raise _forbidden(detail)
    return user


def _unauthorized(detail: str = 'Could not validate credentials') -> HTTPException:
    """Return standardized HTTP 401 response."""
    return HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    """Return standardized HTTP 403 response."""
    return HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=detail)


__all__ = ['get_current_user']
