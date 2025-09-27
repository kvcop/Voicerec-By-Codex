"""Tests for database schema version validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from app.db.schema import ensure_schema_version
from app.db.session import reset_engine_cache

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.mark.asyncio
async def test_ensure_schema_version_matches(db_engine: AsyncEngine) -> None:
    """ensure_schema_version should pass when the stored version matches settings."""
    _ = db_engine
    reset_engine_cache()
    await ensure_schema_version()


@pytest.mark.asyncio
async def test_ensure_schema_version_detects_mismatch(db_engine: AsyncEngine) -> None:
    """ensure_schema_version should raise when the stored version differs."""
    async with db_engine.begin() as connection:
        await connection.execute(
            text('UPDATE alembic_version SET version_num = :version'),
            {'version': '0.0.0'},
        )

    reset_engine_cache()

    with pytest.raises(RuntimeError, match='Database schema version mismatch'):
        await ensure_schema_version()
