"""Custom SQLAlchemy types for application models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import CHAR, TypeDecorator

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect
    from sqlalchemy.sql.type_api import TypeEngine


DatetimeType = datetime


class GUID(TypeDecorator[uuid.UUID | str]):
    """Platform-independent UUID type."""

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:  # type: ignore[override]
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(  # type: ignore[override]
        self, value: uuid.UUID | str | None, dialect: Dialect
    ) -> uuid.UUID | str | None:
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value if dialect.name == 'postgresql' else str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(  # type: ignore[override]
        self, value: uuid.UUID | str | None, _: Dialect
    ) -> uuid.UUID | None:
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))
