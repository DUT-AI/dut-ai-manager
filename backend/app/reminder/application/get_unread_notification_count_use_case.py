"""
Get Unread Notification Count Use Case.
Single-Responsibility Use Case according to Constitution Principle VII.
"""

from app.reminder.application.dtos import UnreadCountDto
from app.reminder.infrastructure.repository import NotificationRepository


class GetUnreadNotificationCountUseCase:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def execute(self, user_id: int) -> UnreadCountDto:
        count = self.notification_repo.get_unread_count(user_id=user_id)
        return UnreadCountDto(unread_count=count)
