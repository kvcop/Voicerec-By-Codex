"""Tests for database session lazy initialization."""

import importlib

import pytest


@pytest.mark.asyncio
async def test_async_session_uses_temp_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure temporary DATABASE_URL is respected when requesting a session."""
    temp_url = 'postgresql+asyncpg://user:pass@localhost/temp_db'
    monkeypatch.setenv('GPU_GRPC_HOST', 'localhost')
    monkeypatch.setenv('GPU_GRPC_PORT', '1234')
    monkeypatch.setenv('DATABASE_URL', temp_url)
    session_module = importlib.import_module('app.db.session')
    importlib.reload(session_module)
    session_module.reset_engine_cache()

    try:
        async with session_module.AsyncSessionLocal() as db_session:
            bind = db_session.bind
            assert bind is not None
            assert bind.url.render_as_string(hide_password=False) == temp_url
    finally:
        session_module.reset_engine_cache()
