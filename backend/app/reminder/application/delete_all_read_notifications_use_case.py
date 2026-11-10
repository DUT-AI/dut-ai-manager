from app.reminder.infrastructure.repository import NotificationRepository


class DeleteAllReadNotificationsUseCase:
    """Xóa tất cả các thông báo đã đọc của user (Hard delete)."""

    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def execute(self, user_id: int) -> int:
        return self.notification_repo.delete_read_by_user(user_id=user_id)
