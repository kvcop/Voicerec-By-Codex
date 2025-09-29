"""Security helpers for authentication and password management."""

from __future__ import annotations

import bcrypt


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
