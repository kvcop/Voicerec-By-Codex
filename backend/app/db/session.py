"""Database session helpers."""

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import get_settings

_engine: Optional[AsyncEngine] = None
_engine_url: Optional[str] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_session_factory_url: Optional[str] = None


def get_engine() -> AsyncEngine:
    """Return a lazily constructed async engine.

    The engine is instantiated on the first call to this function. Subsequent
    calls reuse the cached engine as long as the connection URL remains
    unchanged.

    Returns:
        An ``AsyncEngine`` instance configured with the current database URL.
    """

    global _engine, _engine_url

    database_url = get_settings().database_url
    if _engine is None or _engine_url != database_url:
        _engine = create_async_engine(database_url, echo=True)
        _engine_url = database_url
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return a lazily constructed async session factory.

    Returns:
        An ``async_sessionmaker`` bound to the cached engine.
    """

    global _session_factory, _session_factory_url

    engine = get_engine()
    if _session_factory is None or _session_factory_url != _engine_url:
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
        _session_factory_url = _engine_url
    return _session_factory


def AsyncSessionLocal() -> AsyncSession:  # noqa: N802 - preserve existing name
    """Return an async session using the lazily constructed factory."""

    session_factory = get_session_factory()
    return session_factory()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session.

    Returns:
        An async generator yielding an ``AsyncSession``.
    """

    async with AsyncSessionLocal() as session:
        yield session


def reset_engine_cache() -> None:
    """Reset cached engine and session factory instances.

    This helper disposes of the lazy singletons so tests can swap the
    ``DATABASE_URL`` environment variable before requesting a new session.
    """

    global _engine, _engine_url, _session_factory, _session_factory_url

    _engine = None
    _engine_url = None
    _session_factory = None
    _session_factory_url = None
    get_settings.cache_clear()
