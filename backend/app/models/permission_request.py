from datetime import date as dt_date, time as dt_time
from enum import Enum
from typing import TYPE_CHECKING, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User


class RequestCategory(str, Enum):
    """Permission request category enum"""

    ABSENCE = "vắng sinh hoạt"
    POSTPONE = "tạm hoãn bài tập"
    LATE = "đi trễ sinh hoạt"
    OTHER = "khác"


class PermissionRequest(TimestampMixin, table=True):
    """Permission Request model"""

    __tablename__ = "permission_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    category: RequestCategory = Field(index=True)
    note: str = Field(max_length=500)
    date: dt_date = Field()
    start_time: dt_time = Field()
    end_time: dt_time = Field()

    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "PermissionRequest.created_by==User.id",
            "foreign_keys": "[PermissionRequest.created_by]",
        }
    )
    updater: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "PermissionRequest.updated_by==User.id",
            "foreign_keys": "[PermissionRequest.updated_by]",
        }
    )

    @property
    def user_name(self) -> Optional[str]:
        return self.creator.name if self.creator else None

    @property
    def creator_name(self) -> Optional[str]:
        return self.creator.name if self.creator else None

    @property
    def updater_name(self) -> Optional[str]:
        return self.updater.name if self.updater else None
