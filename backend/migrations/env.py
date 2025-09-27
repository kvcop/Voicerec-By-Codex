"""Alembic environment configuration."""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

# Ensure application packages are importable when Alembic runs standalone.
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.core.settings import get_settings  # noqa: E402
from app.db import Base, import_model_modules  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configure_database_url() -> None:
    if config.get_main_option('sqlalchemy.url'):
        return

    database_url = os.getenv('DATABASE_URL')
    if database_url:
        config.set_main_option('sqlalchemy.url', database_url)
        return

    settings = get_settings()
    config.set_main_option('sqlalchemy.url', settings.database_url)


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    _configure_database_url()
    import_model_modules()
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    _configure_database_url()
    import_model_modules()

    connectable: AsyncEngine | Connection
    section = config.get_section(config.config_ini_section, {})
    url = config.get_main_option('sqlalchemy.url')
    if url is not None and '+async' not in url and url.startswith(('postgresql://', 'mysql://', 'sqlite://')):
        connectable = engine_from_config(  # type: ignore[assignment]
            section,
            prefix='sqlalchemy.',
            poolclass=pool.NullPool,
        )
    else:
        connectable = async_engine_from_config(
            section,
            prefix='sqlalchemy.',
            poolclass=pool.NullPool,
        )

    async def _async_run() -> None:
        if isinstance(connectable, AsyncEngine):
            async with connectable.connect() as connection:
                await connection.run_sync(_run_migrations)
            await connectable.dispose()
        else:
            with connectable.connect() as connection:  # type: ignore[call-arg]
                _run_migrations(connection)

    asyncio.run(_async_run())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
