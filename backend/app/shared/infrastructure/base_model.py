"""
Base ORM model and mixin for pure SQLAlchemy 2.0 entities.

Provides composable mixins:
- SQLAlchemyUuidPrimaryKeyMixin: RFC 9562 UUIDv7 primary key (default=uuid7).
- SQLAlchemyIntPrimaryKeyMixin: Auto-increment integer primary key.
- SQLAlchemyTimestampOnlyMixin: Pure created_at and updated_at UTC timestamps.
- SQLAlchemySoftDeleteMixin: Opt-in is_deleted boolean flag.
- SQLAlchemyAuditMixin: Opt-in created_by and updated_by user IDs.
- SQLAlchemyFullAuditMixin / SQLAlchemyTimestampMixin: Composite mixin for legacy models.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.context import get_current_user_id
from app.shared.domain.uuid_utils import uuid7


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


class SQLAlchemyUuidPrimaryKeyMixin:
    """Mixin providing RFC 9562 UUIDv7 primary key for SQLAlchemy 2.0 models."""

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )


class SQLAlchemyIntPrimaryKeyMixin:
    """Mixin providing auto-increment integer primary key for SQLAlchemy 2.0 models."""

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )


class SQLAlchemyTimestampOnlyMixin:
    """Pure mixin for timezone-aware created_at and updated_at UTC timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )


class SQLAlchemySoftDeleteMixin:
    """Opt-in mixin for soft-deletion (is_deleted boolean column)."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class SQLAlchemyAuditMixin:
    """Opt-in mixin for created_by and updated_by user tracking."""

    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), default=get_current_user_id, nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        default=get_current_user_id,
        onupdate=get_current_user_id,
        nullable=True,
    )


class SQLAlchemyAuditTimestampMixin(
    SQLAlchemyTimestampOnlyMixin,
    SQLAlchemyAuditMixin,
):
    """
    Composite mixin containing timestamps and user audit tracking WITHOUT soft-delete.
    Designed for models using pure physical hard-delete (Meetings, Homeworks, Teams, etc.).
    """

    pass


class SQLAlchemyFullAuditMixin(
    SQLAlchemyTimestampOnlyMixin,
    SQLAlchemySoftDeleteMixin,
    SQLAlchemyAuditMixin,
):
    """
    Composite mixin containing timestamps, soft-delete, and user audit tracking.
    Enables backward compatibility for legacy models.
    """

    @classmethod
    def from_entity(cls, entity: Any) -> Any:
        raise NotImplementedError("Subclasses must implement from_entity")

    def to_entity(self) -> Any:
        raise NotImplementedError("Subclasses must implement to_entity")


# Backward compatibility alias: legacy models import SQLAlchemyTimestampMixin
# which historically included timestamps, soft-delete, and audit fields.
class SQLAlchemyTimestampMixin(SQLAlchemyFullAuditMixin):
    """Legacy composite mixin ensuring 100% backward compatibility."""

    pass
