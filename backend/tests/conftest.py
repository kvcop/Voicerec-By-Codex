"""Test configuration and shared fixtures."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.settings import get_settings
from app.db.base import Base, import_model_modules
from app.db.session import get_session, reset_engine_cache

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncSession


def _build_sqlite_url(database_path: str) -> str:
    """Return SQLite database URL for the provided file path."""
    return f'sqlite+aiosqlite:///{database_path}'


@pytest.fixture
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Return unique SQLite database URL for the current test function."""
    database_dir = tmp_path_factory.mktemp('sqlite-db')
    database_path = database_dir / 'database.db'
    return _build_sqlite_url(database_path.as_posix())


@pytest_asyncio.fixture
async def db_engine(sqlite_test_url: str) -> AsyncIterator[AsyncEngine]:
    """Create a fresh async SQLite engine with initialized schema."""
    previous_database_url = os.environ.get('DATABASE_URL')
    previous_gpu_host = os.environ.get('GPU_GRPC_HOST')
    previous_gpu_port = os.environ.get('GPU_GRPC_PORT')

    os.environ['DATABASE_URL'] = sqlite_test_url
    os.environ.setdefault('GPU_GRPC_HOST', 'localhost')
    os.environ.setdefault('GPU_GRPC_PORT', '50051')

    reset_engine_cache()
    import_model_modules()

    engine = create_async_engine(sqlite_test_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text('CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(64) NOT NULL)')
        )
        await connection.execute(text('DELETE FROM alembic_version'))
        await connection.execute(
            text('INSERT INTO alembic_version (version_num) VALUES (:version)'),
            {'version': get_settings().database_schema_version},
        )

    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.execute(text('DROP TABLE IF EXISTS alembic_version'))
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        reset_engine_cache()

        if previous_database_url is not None:
            os.environ['DATABASE_URL'] = previous_database_url
        else:
            os.environ.pop('DATABASE_URL', None)

        if previous_gpu_host is not None:
            os.environ['GPU_GRPC_HOST'] = previous_gpu_host
        else:
            os.environ.pop('GPU_GRPC_HOST', None)

        if previous_gpu_port is not None:
            os.environ['GPU_GRPC_PORT'] = previous_gpu_port
        else:
            os.environ.pop('GPU_GRPC_PORT', None)


@pytest.fixture
def session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Return async session factory bound to the temporary engine."""
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Provide a transactional session rolled back after each test."""
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def fastapi_app(
    session_factory: async_sessionmaker[AsyncSession],
) -> Iterator[FastAPI]:
    """Return FastAPI application with database dependency overridden."""
    from app.main import app

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.rollback()

    app.dependency_overrides[get_session] = _override_session

    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def fastapi_db_session(fastapi_app: FastAPI) -> AsyncIterator[AsyncSession]:
    """Yield a database session using the FastAPI override for convenience."""
    override = fastapi_app.dependency_overrides[get_session]
    generator = override()

    try:
        session = await generator.__anext__()
    except StopAsyncIteration:  # pragma: no cover - defensive safeguard
        message = 'Database override did not yield a session'
        raise RuntimeError(message) from None

    try:
        yield session
    finally:
        await generator.aclose()


@pytest_asyncio.fixture
async def verify_database_ready(db_session: AsyncSession) -> None:
    """Ensure the transient database is reachable before running dependent tests."""
    result = await db_session.execute(text('SELECT 1'))
    assert result.scalar_one() == 1
