"""Database session helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import get_settings

engine = create_async_engine(get_settings().database_url, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session.

    Returns:
        An async generator yielding an ``AsyncSession``.
    """
    async with AsyncSessionLocal() as session:
        yield session
