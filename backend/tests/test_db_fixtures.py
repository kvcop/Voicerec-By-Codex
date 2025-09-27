"""Tests for asynchronous database fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from app.db.session import get_session

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_db_session_fixture_executes_simple_query(db_session: AsyncSession) -> None:
    """The standalone database session fixture can execute basic SQL."""
    result = await db_session.execute(text('SELECT 1'))
    assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_fastapi_db_override_yields_independent_sessions(fastapi_app: FastAPI) -> None:
    """FastAPI dependency override provides separate sessions per request."""
    override = fastapi_app.dependency_overrides[get_session]

    first_generator = override()
    second_generator = override()

    first_session = await first_generator.__anext__()
    second_session = await second_generator.__anext__()

    try:
        assert first_session is not second_session

        result = await first_session.execute(text('SELECT 1'))
        assert result.scalar_one() == 1

        result = await second_session.execute(text('SELECT 1'))
        assert result.scalar_one() == 1
    finally:
        await first_generator.aclose()
        await second_generator.aclose()
