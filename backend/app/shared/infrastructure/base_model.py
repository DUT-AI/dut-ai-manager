"""
Base ORM model and mixin for both SQLModel and pure SQLAlchemy 2.0 entities.

Allows incremental migration from SQLModel to SQLAlchemy 2.0.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


from app.core.context import get_current_user_id


class SQLAlchemyTimestampMixin:
    """Mixin for created_at, updated_at timestamps and creator tracking using SQLAlchemy 2.0."""

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
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
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

    @classmethod
    def from_entity(cls, entity: Any) -> Any:
        raise NotImplementedError("Subclasses must implement from_entity")

    def to_entity(self) -> Any:
        raise NotImplementedError("Subclasses must implement to_entity")
