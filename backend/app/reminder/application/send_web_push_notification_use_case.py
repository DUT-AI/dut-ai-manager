"""
SendWebPushNotificationUseCase — Single-Responsibility Use Case.
Gửi thông báo đẩy Web Push tới toàn bộ thiết bị đang kích hoạt của một người dùng.
Tự động dọn dẹp các token đã chết hoặc hết hạn (HTTP 404/410).
"""

from loguru import logger

from app.reminder.domain.repository import PushSubscriptionRepository
from app.reminder.infrastructure.web_push_service import (
    DeadTokenException,
    WebPushService,
    WebPushServiceException,
)


class SendWebPushNotificationUseCase:
    """Use Case gửi Web Push Notification tới các thiết bị của user."""

    def __init__(
        self,
        repo: PushSubscriptionRepository,
        web_push_service: WebPushService,
    ):
        self.repo = repo
        self.web_push_service = web_push_service

    def execute(
        self,
        user_id: int,
        title: str,
        body: str,
        action_url: str | None = None,
        tag: str | None = None,
        category: str | None = None,
    ) -> tuple[int, int]:
        """
        Gửi thông báo đẩy tới user.
        :return: (số_thiết_bị_thành_công, số_thiết_bị_thất_bại)
        """
        subscriptions = self.repo.get_active_by_user_id(user_id)
        if not subscriptions:
            logger.debug(f"User {user_id} không có thiết bị Web Push nào đang hoạt động.")
            return 0, 0

        payload = {
            "title": title,
            "body": body,
            "icon": "/icons/icon-192x192.png",
            "badge": "/icons/icon-192x192.png",
            "tag": tag or "general-notification",
            "data": {
                "url": action_url or "/dashboard/notifications",
                "category": category or "SYSTEM",
            },
        }

        sent_count = 0
        failed_count = 0

        for sub in subscriptions:
            try:
                success = self.web_push_service.send_notification(sub, payload)
                if success:
                    sent_count += 1
                    if sub.id:
                        self.repo.update_last_used(sub.id)
                else:
                    failed_count += 1
            except DeadTokenException:
                logger.info(
                    f"Phát hiện dead token (404/410) cho user {user_id}, "
                    f"đang vô hiệu hóa endpoint: {sub.endpoint[:40]}..."
                )
                self.repo.deactivate_endpoint(sub.endpoint)
                failed_count += 1
            except (WebPushServiceException, Exception) as ex:
                logger.warning(
                    f"Lỗi gửi Web Push tới endpoint {sub.endpoint[:40]}...: {ex}"
                )
                failed_count += 1

        return sent_count, failed_count
