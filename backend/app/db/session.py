"""Database session helpers."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import get_settings


@dataclass
class _EngineCache:
    engine: AsyncEngine | None = None
    engine_url: str | None = None
    session_factory: async_sessionmaker[AsyncSession] | None = None
    session_factory_url: str | None = None


_CACHE = _EngineCache()


def get_engine() -> AsyncEngine:
    """Return a lazily constructed async engine.

    The engine is instantiated on the first call to this function. Subsequent
    calls reuse the cached engine as long as the connection URL remains
    unchanged.

    Returns:
        An ``AsyncEngine`` instance configured with the current database URL.
    """
    database_url = get_settings().database_url
    if _CACHE.engine is None or _CACHE.engine_url != database_url:
        _CACHE.engine = create_async_engine(database_url, echo=True)
        _CACHE.engine_url = database_url
    return _CACHE.engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return a lazily constructed async session factory.

    Returns:
        An ``async_sessionmaker`` bound to the cached engine.
    """
    engine = get_engine()
    if _CACHE.session_factory is None or _CACHE.session_factory_url != _CACHE.engine_url:
        _CACHE.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        _CACHE.session_factory_url = _CACHE.engine_url
    return _CACHE.session_factory


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
    _CACHE.engine = None
    _CACHE.engine_url = None
    _CACHE.session_factory = None
    _CACHE.session_factory_url = None
    get_settings.cache_clear()
