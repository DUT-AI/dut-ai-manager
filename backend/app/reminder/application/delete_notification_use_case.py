from app.reminder.infrastructure.repository import NotificationRepository


class DeleteNotificationUseCase:
    """Xóa một thông báo cụ thể thuộc quyền sở hữu của user (Hard delete)."""

    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def execute(self, notification_id: int, user_id: int) -> bool:
        return self.notification_repo.delete_by_id_and_user(
            notification_id=notification_id,
            user_id=user_id,
        )
