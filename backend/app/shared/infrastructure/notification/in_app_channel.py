"""
In-App Notification Channel Adapter.
Persists notifications to the database 'notifications' table via NotificationRepository.
"""

from datetime import datetime, timezone

from loguru import logger

from app.reminder.domain.entity import (
    Notification,
    ReminderStage,
    TaskType,
)
from app.reminder.domain.entity import (
    NotificationCategory as DomainNotificationCategory,
)
from app.reminder.domain.entity import (
    NotificationLevel as DomainNotificationLevel,
)
from app.reminder.infrastructure.repository import NotificationRepository
from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    ChannelType,
    NotificationChannel,
)
from app.shared.infrastructure.notification_payload import NotificationPayload
from app.user.domain.entity import UserEntity as User


class InAppNotificationChannel(NotificationChannel):
    """Channel adapter lưu trữ thông báo vào cơ sở dữ liệu In-App."""

    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.IN_APP

    async def send(
        self, user: User, payload: NotificationPayload
    ) -> ChannelDeliveryResult:
        try:
            assert user.id is not None
            now = datetime.now(timezone.utc)

            cat_str = (
                payload.category.value
                if hasattr(payload.category, "value")
                else str(payload.category)
            )
            category = DomainNotificationCategory(cat_str)

            lvl_str = (
                payload.level.value
                if hasattr(payload.level, "value")
                else str(payload.level)
            )
            level = DomainNotificationLevel(lvl_str)

            task_type = None
            if payload.task_type:
                try:
                    task_type = TaskType(payload.task_type)
                except Exception:
                    task_type = None

            reminder_stage = None
            if payload.reminder_stage:
                try:
                    reminder_stage = ReminderStage(payload.reminder_stage)
                except Exception:
                    reminder_stage = None

            notif_entity = Notification(
                user_id=user.id,
                title=payload.title,
                content=payload.content,
                category=category,
                level=level,
                action_url=payload.action_url,
                is_read=False,
                task_type=task_type,
                task_id=payload.task_id,
                reminder_stage=reminder_stage,
                metadata_json=payload.metadata,
                created_at=now,
            )

            saved_entity = self.notification_repo.add(notif_entity)
            return ChannelDeliveryResult(
                channel=ChannelType.IN_APP,
                success=True,
                status="SAVED",
            )
        except Exception as e:
            logger.error(f"InAppNotificationChannel failed for user {user.id}: {e}")
            return ChannelDeliveryResult(
                channel=ChannelType.IN_APP,
                success=False,
                status="FAILED",
                error_message=str(e),
            )
