"""Tests for authentication API endpoints."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password, verify_password
from app.core.settings import get_settings
from app.db.repositories.user import UserRepository
from app.services.auth import AUTH_SCHEME_BEARER

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_user_creates_account(
    fastapi_app: FastAPI, fastapi_db_session: AsyncSession
) -> None:
    """Registering a new user persists the account and returns the payload."""
    client = TestClient(fastapi_app)
    payload = {'email': 'user@example.com', 'password': 'SecurePass1'}

    response = client.post('/auth/register', json=payload)

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['email'] == payload['email']
    assert UUID(data['id'])

    repository = UserRepository(fastapi_db_session)
    user = await repository.get_by_email(payload['email'])
    assert user is not None
    assert verify_password(payload['password'], user.hashed_password)


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email(
    fastapi_app: FastAPI, fastapi_db_session: AsyncSession
) -> None:
    """Duplicate email registration attempts yield 409 responses."""
    repository = UserRepository(fastapi_db_session)
    email = 'duplicate@example.com'
    await repository.create(email=email, hashed_password=hash_password('ExistingPass1'))
    await fastapi_db_session.commit()

    client = TestClient(fastapi_app)
    response = client.post(
        '/auth/register',
        json={'email': email, 'password': 'AnotherPass1'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': f'User with email {email} already exists'}


@pytest.mark.asyncio
async def test_register_user_validates_password_length(fastapi_app: FastAPI) -> None:
    """Passwords shorter than eight characters are rejected by validation."""
    client = TestClient(fastapi_app)
    response = client.post(
        '/auth/register',
        json={'email': 'short@example.com', 'password': 'short'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_login_user_returns_jwt(
    fastapi_app: FastAPI, fastapi_db_session: AsyncSession
) -> None:
    """Valid credentials yield a signed JWT access token."""
    repository = UserRepository(fastapi_db_session)
    plaintext = 'SuperSecure123'
    user = await repository.create(
        email='auth@example.com', hashed_password=hash_password(plaintext)
    )
    await fastapi_db_session.commit()

    client = TestClient(fastapi_app)
    response = client.post(
        '/auth/login',
        json={'email': user.email, 'password': plaintext},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload['token_type'] == AUTH_SCHEME_BEARER

    settings = get_settings()
    decoded = jwt.decode(
        payload['access_token'],
        settings.auth_secret_key,
        algorithms=[settings.auth_token_algorithm],
    )
    assert decoded['sub'] == str(user.id)
    assert decoded['email'] == user.email


@pytest.mark.asyncio
async def test_login_user_rejects_invalid_credentials(
    fastapi_app: FastAPI, fastapi_db_session: AsyncSession
) -> None:
    """Incorrect password produces a 401 response."""
    repository = UserRepository(fastapi_db_session)
    email = 'wrongpass@example.com'
    await repository.create(email=email, hashed_password=hash_password('CorrectPass123'))
    await fastapi_db_session.commit()

    client = TestClient(fastapi_app)
    response = client.post(
        '/auth/login',
        json={'email': email, 'password': 'IncorrectPass456'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Invalid email or password'}
