"""
Base ORM model mixin for SQLModel entities.

Provides audit fields (created_at, updated_at, created_by, updated_by)
and soft delete support.

This is the INFRASTRUCTURE layer — only ORM models should use this mixin.
Domain entities should NOT import from here.
"""

from datetime import datetime
from typing import Optional

from app.core.context import get_current_user_id
from app.shared.domain.base_entity import BaseEntity
from app.utils.datetime import get_current_utc7_time
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Mixin for created_at, updated_at timestamps and creator tracking."""

    created_at: datetime = Field(default_factory=get_current_utc7_time, index=True)
    updated_at: datetime = Field(
        default_factory=get_current_utc7_time,
        sa_column_kwargs={"onupdate": get_current_utc7_time},
    )
    is_deleted: bool = Field(default=False)
    created_by: Optional[int] = Field(
        default_factory=get_current_user_id, foreign_key="users.id"
    )
    updated_by: Optional[int] = Field(
        default_factory=get_current_user_id,
        foreign_key="users.id",
        sa_column_kwargs={"onupdate": get_current_user_id},
    )

    @classmethod
    def from_entity(cls, entity: BaseEntity) -> "TimestampMixin":
        raise NotImplementedError("Subclasses must implement from_entity")

    def to_entity(self) -> BaseEntity:
        raise NotImplementedError("Subclasses must implement to_entity")
