"""
Mark All Notifications As Read Use Case.
Single-Responsibility Use Case according to Constitution Principle VII.
"""

from app.reminder.infrastructure.repository import NotificationRepository


class MarkAllNotificationsAsReadUseCase:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def execute(self, user_id: int) -> int:
        return self.notification_repo.mark_all_as_read(user_id=user_id)
