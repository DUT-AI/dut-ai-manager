import asyncio

from loguru import logger

from app.bonus_point.domain.events import (
    BonusPointCreated,
    BonusPointDeleted,
    BonusPointUpdated,
)
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.shared.infrastructure.notification_service import NotificationService


class BonusPointNotificationHandler(EventHandler):
    """Xử lý gửi thông báo Discord và Zalo khi điểm cộng được tạo, cập nhật hoặc xóa."""

    def __init__(
        self,
        notification_service: NotificationService,
    ):
        self.notification_service = notification_service

    async def handle(
        self, event: BonusPointCreated | BonusPointUpdated | BonusPointDeleted
    ) -> None:
        """Thông báo cho người dùng trên Discord và Zalo."""
        try:
            logger.info(f"Handling {type(event).__name__} for user_id={event.user_id}")
            asyncio.create_task(self._send_notifications_task(event))
        except Exception as e:
            logger.error(f"Error in BonusPointNotificationHandler: {e}")

    async def _send_notifications_task(
        self, event: BonusPointCreated | BonusPointUpdated | BonusPointDeleted
    ) -> None:
        """Hàm chạy ngầm để gửi thông báo qua NotificationService."""
        try:
            if isinstance(event, BonusPointDeleted):
                payload = NotificationPayload(
                    user_id=event.user_id,
                    title="ℹ️ THÔNG BÁO HỦY ĐIỂM CỘNG",
                    content="Một mục điểm cộng trước đó của bạn đã được hủy trên hệ thống.",
                    category=NotificationCategory.BONUS_POINT,
                    level=NotificationLevel.INFO,
                    image_asset="meme-khoc-2.jpg",
                )
            else:
                display_date = event.date
                if event.date:
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(event.date)
                        if dt.hour == 0 and dt.minute == 0:
                            display_date = dt.strftime("%d/%m/%Y")
                        else:
                            display_date = dt.strftime("%d/%m/%Y lúc %H:%M")
                    except ValueError:
                        pass

                is_created = isinstance(event, BonusPointCreated)
                title = (
                    "🏆 THÔNG BÁO CỘNG ĐIỂM THÀNH TÍCH"
                    if is_created
                    else "📝 THÔNG BÁO CẬP NHẬT ĐIỂM CỘNG"
                )
                actor = (
                    event.creator_name
                    if is_created
                    else getattr(event, "updater_name", "Hệ thống")
                )

                points_prefix = "+" if event.points > 0 else ""
                points_str = f"{points_prefix}{event.points} điểm"

                fields = [
                    {"name": "🌟 Số điểm", "value": points_str, "inline": True},
                    {"name": "📅 Ngày", "value": str(display_date), "inline": True},
                    {"name": "📝 Lý do", "value": event.reason, "inline": False},
                    {
                        "name": "💁‍♂️ Người thực hiện",
                        "value": actor or "Hệ thống",
                        "inline": False,
                    },
                ]

                # Chọn meme tương ứng: Nếu cộng điểm dùng meme ngạc nhiên/vui, nếu trừ điểm dùng meme khóc
                image_asset = (
                    "meme-ngac-nhien.jpeg" if event.points >= 0 else "meme-khoc-2.jpg"
                )

                payload = NotificationPayload(
                    user_id=event.user_id,
                    title=title,
                    content=(
                        f"Chào **{event.user_name or 'bạn'}**!\n"
                        f"Bạn vừa có cập nhật điểm rèn luyện ({points_str}): **{event.reason}**.\n"
                        f"Cùng tiếp tục phát huy nhé!"
                    ),
                    category=NotificationCategory.BONUS_POINT,
                    level=NotificationLevel.SUCCESS
                    if event.points >= 0
                    else NotificationLevel.WARNING,
                    image_asset=image_asset,
                    fields=fields,
                )

            await self.notification_service.send_to_user(payload)
            logger.info(f"Sent bonus point notification for user {event.user_id}")

        except Exception as e:
            logger.error(f"Unexpected error in bonus point notification task: {e}")
