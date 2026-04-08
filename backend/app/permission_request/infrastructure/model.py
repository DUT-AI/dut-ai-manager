from datetime import datetime
from typing import Optional, TYPE_CHECKING, cast

from app.permission_request.domain.entity import (
    PermissionRequest as PermissionRequestEntity,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.infrastructure.base_model import TimestampMixin
from app.shared.domain.base_entity import BaseEntity
from sqlmodel import Field, Index, Relationship

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel
    from app.homework.infrastructure.model import HomeworkModel
    from app.meeting.infrastructure.model import Meeting


class PermissionRequest(TimestampMixin, table=True):
    """Permission Request model"""

    __tablename__ = "permission_requests"
    __table_args__ = (Index("ix_permission_requests_created_by", "created_by"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    category: RequestCategory = Field(index=True)
    note: str = Field(max_length=500)
    start_time: Optional[datetime] = Field(default=None)

    # Specific metadata fields
    homework_id: Optional[int] = Field(
        default=None, foreign_key="homeworks.id", index=True
    )
    meeting_id: Optional[int] = Field(
        default=None, foreign_key="meetings.id", index=True
    )

    # Relationships
    user: "UserModel" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PermissionRequest.created_by]"}
    )
    homework: Optional["HomeworkModel"] = Relationship()
    meeting: Optional["Meeting"] = Relationship()

    def to_entity(self) -> PermissionRequestEntity:
        if self.created_by is None:
            raise ValueError("permission request missing created_by")

        return PermissionRequestEntity(
            id=self.id,
            user_id=self.created_by,
            created_by=self.created_by,
            updated_by=self.updated_by,
            category=self.category,
            note=self.note,
            homework_id=self.homework_id,
            meeting_id=self.meeting_id,
            start_time=self.start_time,
            created_at=self.created_at,
            updated_at=self.updated_at,
            # Map related entities
            user=self.user.to_entity() if self.user else None,
            homework=self.homework.to_entity() if self.homework else None,
            meeting=self.meeting.to_entity() if self.meeting else None,
        )

    @classmethod
    def from_entity(cls, entity: BaseEntity) -> "PermissionRequest":
        """Convert PermissionRequest domain entity to ORM model"""
        if not isinstance(entity, PermissionRequestEntity):
            e = cast(PermissionRequestEntity, entity)
        else:
            e = entity
            
        return cls(
            id=e.id,
            category=e.category,
            note=e.note,
            start_time=e.start_time if e.start_time else None,
            homework_id=e.homework_id,
            meeting_id=e.meeting_id,
            created_by=e.created_by,
            updated_by=e.updated_by,
            created_at=e.created_at,
            updated_at=e.updated_at,
            is_deleted=e.is_deleted,
        )
