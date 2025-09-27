"""Database schema version helpers."""

from __future__ import annotations

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import get_settings
from app.db.session import get_engine


async def _fetch_current_version() -> str | None:
    """Return the current Alembic schema version stored in the database."""
    engine = get_engine()
    async with engine.connect() as connection:
        result = await connection.execute(text('SELECT version_num FROM alembic_version'))
        return result.scalar_one_or_none()


async def ensure_schema_version() -> None:
    """Validate that the database schema matches the expected application version."""
    expected_version = get_settings().database_schema_version

    try:
        current_version = await _fetch_current_version()
    except SQLAlchemyError as exc:  # pragma: no cover - defensive guard
        message = 'Unable to determine database schema version. Did you run migrations?'
        raise RuntimeError(message) from exc

    if current_version is None:
        message = 'Database schema version is missing. Run migrations before starting the API.'
        raise RuntimeError(message)

    if current_version != expected_version:
        message = (
            'Database schema version mismatch. '
            f'Expected "{expected_version}", found "{current_version}". '
            'Run the latest migrations to update the database.'
        )
        raise RuntimeError(message)

    logger.info('database.schema_version.verified', version=current_version)
