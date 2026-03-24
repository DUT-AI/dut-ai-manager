from abc import abstractmethod
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel


class Base(SQLModel):
    """Base class wrapper to alias SQLModel for compatibility."""

    pass


def _utc_now() -> datetime:
    """Return current UTC time as naive datetime (no tzinfo).
    Compatible with PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns.
    """
    return datetime.utcnow()


class TimestampMixin(Base):
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column_kwargs={"onupdate": _utc_now},
    )
    is_deleted: bool = Field(default=False)

    @abstractmethod
    def to_entity(self) -> Any:
        """Kiểm tra Mypy / TypeHint -> Đẩy model về Entity"""
        pass

    @classmethod
    @abstractmethod
    def from_entity(cls, entity: Any) -> "TimestampMixin":
        """Nhận Entity thuần đẩy về Model SQLModel"""
        pass
