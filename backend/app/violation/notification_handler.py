import asyncio
from datetime import datetime

from loguru import logger

from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.violation.domain.events import ViolationCreated


class ViolationNotificationHandler(EventHandler):
    """Xử lý gửi thông báo đa kênh (In-App DB, Discord, Zalo, Web Push) khi có vi phạm mới."""

    def __init__(
        self,
        dispatcher: UnifiedNotificationDispatcher,
    ):
        self.dispatcher = dispatcher

    async def handle(self, event: ViolationCreated) -> None:
        """Thông báo cho người dùng khi có vi phạm mới."""
        try:
            logger.info(f"Handling ViolationCreated for user {event.user_id}")
            asyncio.create_task(self._send_notifications_task(event))
        except Exception as e:
            logger.error(f"Error in ViolationNotificationHandler: {e}")

    async def _send_notifications_task(self, event: ViolationCreated) -> None:
        """Hàm chạy ngầm để gửi thông báo qua UnifiedNotificationDispatcher."""
        try:
            display_date = event.date
            if event.date:
                try:
                    dt = datetime.fromisoformat(event.date)
                    if dt.hour == 0 and dt.minute == 0:
                        display_date = dt.strftime("%d/%m/%Y")
                    else:
                        display_date = dt.strftime("%d/%m/%Y lúc %H:%M")
                except ValueError:
                    pass

            fields = [
                {"name": "📝 Lý do", "value": event.reason, "inline": False},
                {"name": "📅 Ngày vi phạm", "value": str(display_date), "inline": True},
                {
                    "name": "💁‍♂️ Được tạo bởi",
                    "value": event.creator_name or "Hệ thống",
                    "inline": True,
                },
            ]

            payload = NotificationPayload(
                user_id=event.user_id,
                title="⚠️ THÔNG BÁO VI PHẠM KỶ LUẬT",
                content=(
                    f"Chào {event.user_name or 'bạn'}!\n"
                    f"Bạn vừa bị ghi nhận 01 biên bản vi phạm mới trong hệ thống.\n"
                    f"Lý do: {event.reason}.\n"
                    f"Vui lòng kiểm tra và rút kinh nghiệm."
                ),
                category=NotificationCategory.VIOLATION,
                level=NotificationLevel.CRITICAL,
                image_asset="meme-doi-no-2.jpg",
                fields=fields,
                action_url="/violations",
            )

            await self.dispatcher.dispatch(payload)
            logger.info(f"Sent violation notification for user {event.user_id}")

        except Exception as e:
            logger.error(f"Unexpected error in violation notification task: {e}")
