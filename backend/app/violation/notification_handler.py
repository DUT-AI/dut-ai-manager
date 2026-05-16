import asyncio
from typing import cast

from loguru import logger

from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.discord_service import DiscordService
from app.user.infrastructure.repository import UserRepository
from app.violation.domain.events import ViolationCreated
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class ViolationNotificationHandler(EventHandler):
    """Xử lý gửi thông báo Discord và Zalo khi có vi phạm mới."""

    def __init__(
        self,
        discord_service: DiscordService,
        zalo_bot: ZaloBotClient,
        user_repo: UserRepository,
    ):
        self.discord_service = discord_service
        self.zalo_bot = zalo_bot
        self.user_repo = user_repo

    async def handle(self, event: ViolationCreated) -> None:
        """Thông báo cho người dùng trên Discord và Zalo khi có vi phạm mới."""
        try:
            logger.info(f"Handling ViolationCreated for user {event.user_id}")

            asyncio.create_task(self._send_notifications_task(event))

            logger.info(
                f"Triggered background job for ViolationNotification: user_id={event.user_id}"
            )
        except Exception as e:
            logger.error(f"Error in ViolationNotificationHandler: {e}")

    async def _send_notifications_task(self, event: ViolationCreated) -> None:
        """Hàm chạy ngầm để gửi thông báo qua Discord và Zalo."""
        try:
            # 0. Fetch user to get notification IDs (kept lightweight in Event)
            user = self.user_repo.get_by_id(event.user_id)
            if not user:
                logger.warning(
                    f"Background: Could not find user {event.user_id} for violation notification"
                )
                return

            user_discord_id = user.discord_id
            user_zalo_bot_id = user.zalo_bot_id

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

            # 1. Discord Embed
            embed = {
                "title": "⚠️ THÔNG BÁO VI PHẠM",
                "description": f"Chào **{event.user_name or 'bạn'}**, bạn vừa nhận được một thông báo vi phạm mới.",
                "color": 0xE74C3C,  # Red
                "fields": [
                    {"name": "📝 Lý do", "value": event.reason, "inline": False},
                    {"name": "📅 Ngày vi phạm", "value": display_date, "inline": False},
                    {
                        "name": "💁‍♂️ Được tạo bởi",
                        "value": event.creator_name or "Hệ thống",
                        "inline": False,
                    },
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống nhắc nhở tự động"},
            }

            # 2. Zalo Text
            zalo_text = (
                "⚠️ THÔNG BÁO VI PHẠM\n\n"
                f"Chào {event.user_name or 'bạn'},\n"
                f"Lý do: {event.reason}\n"
                f"Ngày: {display_date}\n"
                f"Người tạo: {event.creator_name or 'Hệ thống'}\n\n"
                "Vui lòng kiểm tra lại và rút kinh nghiệm lần sau."
            )

            # --- Gửi Discord ---
            if user_discord_id:
                try:
                    await self.discord_service.send_message_to_user(
                        user_id=cast(str, user_discord_id),
                        content=f"Chào <@{user_discord_id}>! Bạn có thông báo vi phạm mới.",
                        embed=embed,
                    )
                    logger.info(
                        f"Background: Sent Discord violation notification to {event.user_name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Background: Failed to send Discord violation notification to {event.user_name}: {e}"
                    )

            # --- Gửi Zalo ---
            if user_zalo_bot_id:
                try:
                    await self.zalo_bot.send_message(
                        chat_id=user_zalo_bot_id, text=zalo_text
                    )
                    logger.info(
                        f"Background: Sent Zalo violation notification to {event.user_name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Background: Failed to send Zalo violation notification to {event.user_name}: {e}"
                    )

        except Exception as e:
            logger.error(
                f"Unexpected error in background violation notification task: {e}"
            )
