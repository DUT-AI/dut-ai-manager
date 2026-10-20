"""
SQLAlchemy ORM Model for Notifications.
Unified table 'notifications' supporting both user-facing notification feeds
and internal reminder tracking/deduplication.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.reminder.domain.entity import (
    Notification,
    NotificationCategory,
    NotificationLevel,
    ReminderStage,
    ReminderStatus,
    TaskType,
)
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin


class NotificationModel(Base, SQLAlchemyTimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="SYSTEM")
    level: Mapped[str] = mapped_column(String(50), nullable=False, default="INFO")
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Technical metadata for reminder engine, deduplication and audit logging
    task_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reminder_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discord_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_notif_user_unread", "user_id", "is_read", "created_at"),
        Index(
            "idx_notif_dedup",
            "task_type",
            "task_id",
            "user_id",
            "reminder_stage",
        ),
        Index("idx_notif_user_created", "user_id", "created_at"),
    )

    def to_entity(self) -> Notification:
        return Notification(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            content=self.content,
            category=NotificationCategory(self.category),
            level=NotificationLevel(self.level),
            action_url=self.action_url,
            is_read=self.is_read,
            read_at=self.read_at,
            task_type=TaskType(self.task_type) if self.task_type else None,
            task_id=self.task_id,
            reminder_stage=ReminderStage(self.reminder_stage) if self.reminder_stage else None,
            discord_status=ReminderStatus(self.discord_status) if self.discord_status else None,
            error_message=self.error_message,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: Notification) -> "NotificationModel":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            content=entity.content,
            category=entity.category.value,
            level=entity.level.value,
            action_url=entity.action_url,
            is_read=entity.is_read,
            read_at=entity.read_at,
            task_type=entity.task_type.value if entity.task_type else None,
            task_id=entity.task_id,
            reminder_stage=entity.reminder_stage.value if entity.reminder_stage else None,
            discord_status=entity.discord_status.value if entity.discord_status else None,
            error_message=entity.error_message,
            created_at=entity.created_at,
        )
