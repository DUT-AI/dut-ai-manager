from datetime import datetime
from typing import Optional

from app.core.context import get_current_user_id
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
