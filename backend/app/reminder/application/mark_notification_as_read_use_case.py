"""
Mark Notification As Read Use Case.
Single-Responsibility Use Case according to Constitution Principle VII.
"""

from app.reminder.application.dtos import NotificationDto
from app.reminder.infrastructure.repository import NotificationRepository


class MarkNotificationAsReadUseCase:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def execute(self, notification_id: int, user_id: int) -> NotificationDto | None:
        entity = self.notification_repo.mark_as_read(
            notification_id=notification_id,
            user_id=user_id,
        )
        if entity:
            return NotificationDto.model_validate(entity)
        return None
