"""
Violation Notification Handler — reacts to ViolationCreated events.

Sends Discord DM to the violated user.
This replaces the direct NotificationService.send_violation_notification() call.
"""

from app.core.config import settings
from app.core.discord_service import DiscordService
from app.violation.domain.events import ViolationCreated
from loguru import logger


def create_violation_notification_handler(discord_service: DiscordService):
    """Factory: creates handler with injected Discord service."""

    async def handle_violation_created(event: ViolationCreated) -> None:
        """Send Discord DM when a violation is created."""
        try:
            if not event.user_discord_id:
                logger.debug(
                    f"User {event.user_id} has no discord_id, skipping notification"
                )
                return

            embed = {
                "title": "⚠️ Thông báo vi phạm",
                "description": (
                    f"Chào **{event.user_name or 'bạn'}**, "
                    f"bạn vừa nhận được một thông báo vi phạm mới."
                ),
                "color": 0xE74C3C,  # Red
                "fields": [
                    {"name": "📝 Lý do", "value": event.reason, "inline": False},
                    {
                        "name": "📅 Ngày vi phạm",
                        "value": event.date,
                        "inline": False,
                    },
                    {
                        "name": "💁‍♂️ Được tạo bởi",
                        "value": event.creator_name or "Hệ thống",
                        "inline": False,
                    },
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống nhắc nhở tự động"},
            }

            await discord_service.send_message_to_user(
                user_id=event.user_discord_id,
                content="",
                embed=embed,
            )
            logger.info(
                f"Sent violation notification to user {event.user_name} "
                f"(Discord: {event.user_discord_id})"
            )
        except Exception as e:
            logger.error(f"Failed to send violation notification: {e}")

    return handle_violation_created
