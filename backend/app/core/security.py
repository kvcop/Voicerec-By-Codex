"""Security helpers for authentication and password management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

import bcrypt
import jwt

from app.core.settings import get_settings


def hash_password(password: str) -> str:
    """Return a securely hashed representation of ``password``."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Return whether ``password`` matches ``hashed_password``."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        # Raised when ``hashed_password`` is not a valid bcrypt hash.
        return False


def create_access_token(
    *,
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: Mapping[str, Any] | None = None,
) -> str:
    """Return a signed JWT access token for the provided subject."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire_at = now + (expires_delta or timedelta(minutes=settings.auth_token_expire_minutes))

    payload: dict[str, Any] = {
        'sub': subject,
        'iat': int(now.timestamp()),
        'exp': int(expire_at.timestamp()),
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.auth_secret_key,
        algorithm=settings.auth_token_algorithm,
    )
