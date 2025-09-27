"""Declarative base configuration for ORM models."""

from __future__ import annotations

import importlib
import pkgutil

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION: dict[str, str] = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}
"""Naming convention shared across all database constraints."""


metadata = MetaData(naming_convention=NAMING_CONVENTION)
"""Global SQLAlchemy metadata configured with naming conventions."""


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    metadata = metadata


def _iter_model_modules() -> list[str]:
    """Return fully qualified module names for all model modules.

    Returns:
        A list with module names found under ``app.models``.
    """
    package = importlib.import_module('app.models')
    prefix = f'{package.__name__}.'
    return [module_info.name for module_info in pkgutil.walk_packages(package.__path__, prefix)]


def import_model_modules() -> None:
    """Import every model module so SQLAlchemy registers mapped classes."""
    for module_name in _iter_model_modules():
        importlib.import_module(module_name)
