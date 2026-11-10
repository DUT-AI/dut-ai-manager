from datetime import UTC, datetime, timedelta

from app.reminder.infrastructure.repository import NotificationRepository


class CleanExpiredNotificationsUseCase:
    """Tự động dọn dẹp các thông báo đã đọc cũ hơn số ngày retention (TTL Housekeeping)."""

    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def execute(self, retention_days: int = 30) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        return self.notification_repo.delete_read_before(cutoff=cutoff)
