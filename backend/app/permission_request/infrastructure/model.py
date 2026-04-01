from datetime import date as dt_date
from datetime import time as dt_time
from typing import Optional

from app.permission_request.domain.entity import \
  PermissionRequest as PermissionRequestEntity
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.infrastructure.base_model import TimestampMixin
from sqlmodel import Field, Index, SQLModel


class PermissionRequest(TimestampMixin, table=True):
    """Permission Request model"""

    __tablename__ = "permission_requests"
    __table_args__ = (Index("ix_permission_requests_created_by", "created_by"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    category: RequestCategory = Field(index=True)
    note: str = Field(max_length=500)
    date: dt_date = Field(index=True)
    start_time: dt_time = Field()
    end_time: dt_time = Field()

    def to_entity(self) -> PermissionRequestEntity:
        if self.created_by is None:
            raise ValueError("permission request missing created_by")
        return PermissionRequestEntity(
            id=self.id,
            user_id=self.created_by,
            category=self.category,
            date=self.date,
            reason=self.note,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: PermissionRequestEntity) -> "PermissionRequest":
        return cls(
            id=entity.id,
            category=entity.category,
            note=entity.reason,
            date=entity.date,
            start_time=dt_time(0, 0, 0),
            end_time=dt_time(23, 59, 59),
            created_by=entity.user_id,
        )
