import asyncio
from typing import cast

from loguru import logger

from app.bonus_point.domain.events import (
    BonusPointCreated,
    BonusPointDeleted,
    BonusPointUpdated,
)
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.discord_service import DiscordService
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class BonusPointNotificationHandler(EventHandler):
    """Xử lý gửi thông báo Discord và Zalo khi điểm cộng được tạo, cập nhật hoặc xóa."""

    def __init__(
        self,
        discord_service: DiscordService,
        zalo_bot: ZaloBotClient,
        user_repo: UserRepository,
    ):
        self.discord_service = discord_service
        self.zalo_bot = zalo_bot
        self.user_repo = user_repo

    async def handle(
        self, event: BonusPointCreated | BonusPointUpdated | BonusPointDeleted
    ) -> None:
        """Thông báo cho người dùng trên Discord và Zalo."""
        try:
            logger.info(
                f"Handling {type(event).__name__} for user_id={event.user_id}"
            )

            asyncio.create_task(self._send_notifications_task(event))

            logger.info(
                f"Triggered background job for BonusPointNotification: user_id={event.user_id}"
            )
        except Exception as e:
            logger.error(f"Error in BonusPointNotificationHandler: {e}")

    async def _send_notifications_task(
        self, event: BonusPointCreated | BonusPointUpdated | BonusPointDeleted
    ) -> None:
        """Hàm chạy ngầm để gửi thông báo qua Discord và Zalo."""
        try:
            user = self.user_repo.get_by_id(event.user_id)
            if not user:
                logger.warning(
                    f"Background: Could not find user {event.user_id} for bonus point notification"
                )
                return

            user_discord_id = user.discord_id
            user_zalo_bot_id = user.zalo_bot_id

            if isinstance(event, BonusPointDeleted):
                # Xử lý sự kiện xóa
                embed = {
                    "title": "ℹ️ THÔNG BÁO HỦY ĐIỂM CỘNG",
                    "description": f"Chào **{user.name}**, một mục điểm cộng của bạn đã được hủy.",
                    "color": 0x95A5A6,  # Gray
                    "footer": {"text": "DUT AI Manager • Hệ thống nhắc nhở tự động"},
                }
                zalo_text = (
                    "ℹ️ THÔNG BÁO HỦY ĐIỂM CỘNG\n\n"
                    f"Chào {user.name},\n"
                    "Một mục điểm cộng trước đó của bạn đã được hủy trên hệ thống."
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
                title = "🏆 THÔNG BÁO CỘNG ĐIỂM" if is_created else "📝 THÔNG BÁO CẬP NHẬT ĐIỂM CỘNG"
                actor = event.creator_name if is_created else getattr(event, "updater_name", "Hệ thống")

                embed = {
                    "title": title,
                    "description": f"Chúc mừng **{event.user_name or user.name}**, bạn vừa được cộng điểm thành tích!",
                    "color": 0x2ECC71,  # Green
                    "fields": [
                        {"name": "🌟 Số điểm", "value": f"+{event.points} điểm", "inline": True},
                        {"name": "📅 Ngày", "value": display_date, "inline": True},
                        {"name": "📝 Lý do", "value": event.reason, "inline": False},
                        {
                            "name": "💁‍♂️ Được thực hiện bởi",
                            "value": actor or "Hệ thống",
                            "inline": False,
                        },
                    ],
                    "footer": {"text": "DUT AI Manager • Hệ thống khen thưởng & nhắc nhở"},
                }

                zalo_text = (
                    f"{title}\n\n"
                    f"Chào {event.user_name or user.name},\n"
                    f"Số điểm: +{event.points} điểm\n"
                    f"Lý do: {event.reason}\n"
                    f"Ngày: {display_date}\n"
                    f"Thực hiện bởi: {actor or 'Hệ thống'}\n\n"
                    "Cùng tiếp tục phát huy nhé!"
                )

            # --- Gửi Discord ---
            if user_discord_id:
                try:
                    await self.discord_service.send_message_to_user(
                        user_id=cast(str, user_discord_id),
                        content=f"Chào <@{user_discord_id}>! Bạn có thông báo điểm cộng mới.",
                        embed=embed,
                    )
                    logger.info(
                        f"Background: Sent Discord bonus point notification to {user.name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Background: Failed to send Discord bonus point notification to {user.name}: {e}"
                    )

            # --- Gửi Zalo ---
            if user_zalo_bot_id:
                try:
                    await self.zalo_bot.send_message(
                        chat_id=user_zalo_bot_id, text=zalo_text
                    )
                    logger.info(
                        f"Background: Sent Zalo bonus point notification to {user.name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Background: Failed to send Zalo bonus point notification to {user.name}: {e}"
                    )

        except Exception as e:
            logger.error(
                f"Unexpected error in background bonus point notification task: {e}"
            )
