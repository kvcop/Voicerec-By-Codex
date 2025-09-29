"""Authentication API endpoints."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.services.auth import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    LoginResult,
    get_auth_service,
)

if TYPE_CHECKING:
    from app.models.user import User

router = APIRouter(prefix='/auth', tags=['auth'])


class RegisterRequest(BaseModel):
    """Request payload for the registration endpoint."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    """Response schema returned after successful registration."""

    id: str
    email: EmailStr

    @classmethod
    def from_user(cls, user: User) -> RegisterResponse:
        """Return response constructed from the provided ``User`` instance."""
        return cls(id=str(user.id), email=user.email)


class LoginRequest(BaseModel):
    """Request payload for the login endpoint."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(BaseModel):
    """Response schema returned after successful authentication."""

    access_token: str
    token_type: Literal['bearer']

    @classmethod
    def from_result(cls, result: LoginResult) -> LoginResponse:
        """Return response generated from :class:`LoginResult`."""
        return cls(access_token=result.access_token, token_type=result.token_type)


@router.post('/register', status_code=HTTPStatus.CREATED, response_model=RegisterResponse)
async def register_user(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> RegisterResponse:
    """Create a new user account using the supplied credentials."""
    try:
        user = await service.register_user(email=payload.email, password=payload.password)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(exc)) from exc
    return RegisterResponse.from_user(user)


@router.post('/login', response_model=LoginResponse)
async def login_user(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """Authenticate user credentials and return a JWT access token."""
    try:
        result = await service.login_user(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=str(exc)) from exc
    return LoginResponse.from_result(result)
