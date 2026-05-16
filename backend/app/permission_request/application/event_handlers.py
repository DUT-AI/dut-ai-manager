import asyncio

from loguru import logger

from app.core.config import settings
from app.permission_request.domain.events import PermissionRequestCreated
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.discord_service import DiscordService
from app.user.infrastructure.repository import UserRepository


class PermissionRequestNotificationHandler(EventHandler[PermissionRequestCreated]):
    """Xử lý gửi thông báo vào room Discord khi có yêu cầu xin phép mới."""

    def __init__(
        self,
        discord_service: DiscordService,
        user_repo: UserRepository,
    ):
        self.discord_service = discord_service
        self.user_repo = user_repo

    async def handle(self, event: PermissionRequestCreated) -> None:
        try:
            logger.info(
                f"Handling PermissionRequestCreated for notification: {event.request_id}"
            )
            user = self.user_repo.get_by_id(event.user_id)
            if not user:
                logger.error(
                    f"User {event.user_id} not found for permission request {event.request_id}"
                )
                return

            # Chạy ngầm việc gửi thông báo
            asyncio.create_task(self._send_notification_task(event, user))
        except Exception as e:
            logger.error(f"Error in PermissionRequestNotificationHandler: {e}")

    async def _send_notification_task(
        self, event: PermissionRequestCreated, user
    ) -> None:
        try:
            room_id = settings.DISCORD_PERMISSION_ROOM_ID
            if not room_id:
                logger.warning("DISCORD_PERMISSION_ROOM_ID is not configured.")
                return
            match event.category:
                case RequestCategory.ABSENCE:
                    category_text = "Vắng sinh hoạt"
                case RequestCategory.POSTPONE:
                    category_text = "Tạm hoãn bài tập"
                case RequestCategory.LATE:
                    category_text = "Xin đi trễ"
                case RequestCategory.OTHER:
                    category_text = "Khác"
                case _:
                    category_text = "Không xác định"

            fields = [
                {"name": "Người yêu cầu", "value": user.name, "inline": False},
            ]

            if event.start_time:
                time_str = event.start_time.strftime("%d/%m/%Y %H:%M")
                fields.append(
                    {"name": "Thời gian/Hạn", "value": time_str, "inline": False}
                )

            fields.append(
                {
                    "name": "Lý do",
                    "value": event.note or "Không có",
                    "inline": False,
                }
            )

            embed = {
                "title": f"📋 YÊU CẦU XIN PHÉP MỚI: {category_text.upper()}",
                "color": 0xF39C12,  # Orange
                "fields": fields,
                "footer": {"text": f"Mã yêu cầu: {event.request_id} • DUT AI Manager"},
            }

            await self.discord_service.send_message_to_room(
                channel_id=room_id,
                embed=embed,
            )
            logger.info(
                f"Background: Sent Discord room notification for permission request {event.request_id}"
            )

        except Exception as e:
            logger.error(
                f"Unexpected error in background permission notification task: {e}"
            )
