"""Integration tests validating Alembic migrations."""

from __future__ import annotations

from collections.abc import Generator, Iterable, Sequence
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import Script, ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from typing import cast

from app.db import Base, import_model_modules


BACKEND_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = BACKEND_DIR / 'alembic.ini'
MIGRATIONS_PATH = BACKEND_DIR / 'migrations'


def _base_alembic_config() -> Config:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option('script_location', str(MIGRATIONS_PATH))
    config.attributes['configure_logger'] = False
    return config


def _make_alembic_config(database_url: str) -> Config:
    config = _base_alembic_config()
    config.set_main_option('sqlalchemy.url', database_url)
    return config


def _iter_revisions() -> Iterable[Script]:
    script_directory = ScriptDirectory.from_config(_base_alembic_config())
    revisions = list(script_directory.walk_revisions('base', 'heads'))
    revisions.reverse()
    return revisions


@pytest.fixture(scope='session', autouse=True)
def load_models() -> None:
    """Ensure model metadata is imported once before running migration tests."""

    import_model_modules()


@pytest.fixture()
def sqlite_database_url(tmp_path: Path) -> str:
    """Create file-backed SQLite database URL for Alembic operations."""

    database_path = tmp_path / 'alembic-migration.db'
    return f'sqlite:///{database_path.as_posix()}'


@pytest.fixture()
def sync_engine(sqlite_database_url: str) -> Generator[Engine, None, None]:
    """Provide synchronous engine bound to the temporary SQLite database."""

    engine = create_engine(sqlite_database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def alembic_config(sqlite_database_url: str) -> Config:
    """Alembic configuration bound to a temporary SQLite database."""

    return _make_alembic_config(sqlite_database_url)


@pytest.mark.parametrize('revision', _iter_revisions())
def test_migrations_stairway(alembic_config: Config, revision: Script) -> None:
    """Each migration can be upgraded and downgraded sequentially."""

    upgrade(alembic_config, revision.revision)

    if isinstance(revision.down_revision, Sequence):
        target_revision = cast(str, revision.down_revision[0])
    else:
        target_revision = cast(str, revision.down_revision or '-1')

    downgrade(alembic_config, target_revision)

    upgrade(alembic_config, revision.revision)


def test_migrations_match_metadata(alembic_config: Config, sync_engine: Engine) -> None:
    """The database schema produced by migrations matches SQLAlchemy metadata."""

    upgrade(alembic_config, 'head')

    try:
        with sync_engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={
                    'target_metadata': Base.metadata,
                    'compare_type': True,
                    'compare_server_default': True,
                },
            )
            diff = compare_metadata(context, Base.metadata)

        assert diff == []
    finally:
        downgrade(alembic_config, 'base')
