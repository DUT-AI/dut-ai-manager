"""
Permission Request ORM Model — SQLAlchemy 2.0, infrastructure layer.
"""

from datetime import datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.permission_request.domain.entity import (
    PermissionRequest as PermissionRequestEntity,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin

if TYPE_CHECKING:
    from app.homework.infrastructure.model import HomeworkModel
    from app.meeting.infrastructure.model import Meeting
    from app.user.infrastructure.model import UserModel


class PermissionRequest(SQLAlchemyTimestampMixin, Base):
    """Permission Request model"""

    __tablename__ = "permission_requests"
    __table_args__ = (Index("ix_permission_requests_created_by", "created_by"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[RequestCategory] = mapped_column(String(100), index=True)
    note: Mapped[str] = mapped_column(String(500))
    start_time: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # Specific metadata fields
    homework_id: Mapped[int | None] = mapped_column(
        ForeignKey("homeworks.id"), default=None, index=True
    )
    meeting_id: Mapped[int | None] = mapped_column(
        ForeignKey("meetings.id"), default=None, index=True
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        foreign_keys="PermissionRequest.created_by",
        overlaps="creator",
    )
    homework: Mapped["HomeworkModel | None"] = relationship()
    meeting: Mapped["Meeting | None"] = relationship()
    creator: Mapped["UserModel | None"] = relationship(
        foreign_keys="PermissionRequest.created_by",
        overlaps="user",
    )
    updater: Mapped["UserModel | None"] = relationship(
        foreign_keys="PermissionRequest.updated_by",
    )

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
            owner=(
                UserRef(
                    id=self.user.id,
                    name=self.user.name,
                    avatar_url=self.user.avatar_url,
                )
                if self.user
                else None
            ),
            creator=(
                UserRef(
                    id=self.creator.id,
                    name=self.creator.name,
                    avatar_url=self.creator.avatar_url,
                )
                if self.creator
                else None
            ),
            updater=(
                UserRef(
                    id=self.updater.id,
                    name=self.updater.name,
                    avatar_url=self.updater.avatar_url,
                )
                if self.updater
                else None
            ),
            homework=self.homework.to_entity() if self.homework else None,
            meeting=self.meeting.to_entity() if self.meeting else None,
        )

    @classmethod
    def from_entity(cls, entity: PermissionRequestEntity) -> "PermissionRequest":
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
