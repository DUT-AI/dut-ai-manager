"""
Get My Notifications Use Case.
Single-Responsibility Use Case according to Constitution Principle VII.
"""

from app.reminder.application.dtos import NotificationDto
from app.reminder.domain.entity import NotificationCategory
from app.reminder.infrastructure.repository import NotificationRepository


class GetMyNotificationsUseCase:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def execute(
        self,
        user_id: int,
        category: NotificationCategory | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[NotificationDto], int]:
        entities, total = self.notification_repo.get_user_notifications(
            user_id=user_id,
            category=category,
            is_read=is_read,
            page=page,
            page_size=page_size,
        )
        dtos = [NotificationDto.model_validate(e) for e in entities]
        return dtos, total
