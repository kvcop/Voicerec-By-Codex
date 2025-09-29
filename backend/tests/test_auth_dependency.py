"""Tests for JWT authentication dependency."""

from __future__ import annotations

from datetime import timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.repositories.user import UserRepository
from app.services.transcript import resolve_raw_audio_dir

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User

AUTH_HEADER_NAME = 'Authorization'
BEARER_PREFIX = 'Bearer'


async def _create_user(
    session: AsyncSession,
    *,
    email: str = 'jwt-user@example.com',
    password: str | None = None,
) -> User:
    """Persist and return a user for authentication tests."""
    repository = UserRepository(session)
    secret = password or 'StrongPass123'
    user = await repository.create(email=email, hashed_password=hash_password(secret))
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_meeting_upload_requires_authorization(
    fastapi_app: FastAPI,
) -> None:
    """Uploading audio without credentials returns a 401 error."""
    client = TestClient(fastapi_app)
    response = client.post(
        '/api/meeting/upload',
        files={'file': ('meeting.wav', b'RIFF', 'audio/wav')},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.asyncio
async def test_meeting_upload_rejects_invalid_token(
    fastapi_app: FastAPI,
) -> None:
    """Invalid JWT tokens trigger a 401 response."""
    client = TestClient(fastapi_app)
    response = client.post(
        '/api/meeting/upload',
        headers={AUTH_HEADER_NAME: f'{BEARER_PREFIX} invalid-token'},
        files={'file': ('meeting.wav', b'RIFF', 'audio/wav')},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.asyncio
async def test_meeting_upload_rejects_expired_token(
    fastapi_app: FastAPI,
    fastapi_db_session: AsyncSession,
) -> None:
    """Expired tokens are rejected by the dependency."""
    user = await _create_user(fastapi_db_session)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(seconds=-1),
        additional_claims={'email': user.email},
    )

    client = TestClient(fastapi_app)
    response = client.post(
        '/api/meeting/upload',
        headers={AUTH_HEADER_NAME: f'{BEARER_PREFIX} {access_token}'},
        files={'file': ('meeting.wav', b'RIFF', 'audio/wav')},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Token has expired'}


@pytest.mark.asyncio
async def test_meeting_upload_rejects_unknown_user(
    fastapi_app: FastAPI,
) -> None:
    """Tokens referencing absent users yield 403 responses."""
    token = create_access_token(subject=str(uuid4()))

    client = TestClient(fastapi_app)
    response = client.post(
        '/api/meeting/upload',
        headers={AUTH_HEADER_NAME: f'{BEARER_PREFIX} {token}'},
        files={'file': ('meeting.wav', b'RIFF', 'audio/wav')},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'User account is not permitted to access this resource'}


@pytest.mark.asyncio
async def test_meeting_upload_accepts_valid_token(
    fastapi_app: FastAPI,
    fastapi_db_session: AsyncSession,
) -> None:
    """Valid JWT tokens allow access to the meeting upload endpoint."""
    user = await _create_user(fastapi_db_session)
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={'email': user.email},
    )

    client = TestClient(fastapi_app)
    response = client.post(
        '/api/meeting/upload',
        headers={AUTH_HEADER_NAME: f'{BEARER_PREFIX} {access_token}'},
        files={'file': ('meeting.wav', b'RIFF', 'audio/wav')},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    raw_dir = resolve_raw_audio_dir()
    stored_file = raw_dir / f'{payload["meeting_id"]}.wav'
    assert stored_file.exists()
    stored_file.unlink()


@pytest.mark.asyncio
async def test_meeting_stream_requires_authorization(fastapi_app: FastAPI) -> None:
    """Accessing the streaming endpoint without credentials returns 401."""
    client = TestClient(fastapi_app)
    response = client.get('/api/meeting/some-id/stream')

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.asyncio
async def test_meeting_stream_allows_authorized_request(
    fastapi_app: FastAPI,
    fastapi_db_session: AsyncSession,
) -> None:
    """Authorized requests reach business logic even if meeting is missing."""
    user = await _create_user(fastapi_db_session)
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={'email': user.email},
    )

    client = TestClient(fastapi_app)
    response = client.get(
        '/api/meeting/nonexistent/stream',
        headers={AUTH_HEADER_NAME: f'{BEARER_PREFIX} {access_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Meeting not found'}
