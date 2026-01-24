from app.models import Violation, Homework, User
from app.core.config import settings
from app.core.discord_service import DiscordService
from app.models.permission_request import PermissionRequest, RequestCategory
from loguru import logger


class NotificationService:
    """Service for handling system-wide notifications."""

    def __init__(self, discord_service: DiscordService):
        self.discord_service = discord_service

    async def send_permission_request_notification(
        self, request: PermissionRequest
    ) -> None:
        """Send a rich Discord notification for a new permission request."""
        try:
            category_map = {
                RequestCategory.ABSENCE: ("🚫 Xin vắng sinh hoạt", 0xE74C3C),  # Red
                RequestCategory.POSTPONE: (
                    "⏰ Xin tạm hoãn bài tập",
                    0xF1C40F,
                ),  # Yellow
                RequestCategory.OTHER: ("🏃 Khác", 0x3498DB),  # Blue
                RequestCategory.LATE: ("⏱️ Xin đến muộn", 0x9B59B6),  # Purple
            }
            category_info = category_map.get(
                request.category, (str(request.category), 0x95A5A6)
            )
            category_text, color = category_info

            # Get user info
            user = request.creator
            user_name = user.name if user else f"User #{request.created_by}"

            embed = {
                "title": "📋 Yêu cầu xin phép mới",
                "description": "Có một yêu cầu mới cần được xem xét.",
                "color": color,
                "fields": [
                    {"name": "👤 Người gửi", "value": user_name, "inline": False},
                    {
                        "name": "📌 Loại yêu cầu",
                        "value": category_text,
                        "inline": True,
                    },
                    {
                        "name": "📅 Ngày xin phép",
                        "value": request.date.strftime("%d/%m/%Y"),
                        "inline": True,
                    },
                    {
                        "name": "\u200b",
                        "value": "\u200b",
                        "inline": True,
                    },  # Force new line
                    {
                        "name": "⏰ Bắt đầu",
                        "value": (
                            request.start_time.strftime("%H:%M")
                            if request.start_time
                            else "N/A"
                        ),
                        "inline": True,
                    },
                    {
                        "name": "⏱️ Kết thúc",
                        "value": (
                            request.end_time.strftime("%H:%M")
                            if request.end_time
                            else "N/A"
                        ),
                        "inline": True,
                    },
                    {
                        "name": "\u200b",
                        "value": "\u200b",
                        "inline": True,
                    },  # For alignment
                    {
                        "name": "📝 Lý do / Ghi chú",
                        "value": request.note or "Không có",
                        "inline": False,
                    },
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống thông báo tự động"},
            }

            await self.discord_service.send_message_to_room(
                channel_id=settings.DISCORD_PERMISSION_ROOM_ID,
                embed=embed,
            )
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    async def send_violation_notification(self, violation: Violation) -> None:
        """Send a direct message to the user about their violation."""
        try:
            user = violation.user
            if not user or not user.discord_id:
                logger.debug(
                    f"User {violation.user_id} has no discord_id, skipping notification"
                )
                return

            embed = {
                "title": "⚠️ Thông báo vi phạm",
                "description": f"Chào **{user.name}**, bạn vừa nhận được một thông báo vi phạm mới.",
                "color": 0xE74C3C,  # Red
                "fields": [
                    {"name": "📝 Lý do", "value": violation.reason, "inline": False},
                    {
                        "name": "📅 Ngày vi phạm",
                        "value": violation.date.strftime("%H:%M %d/%m/%Y"),
                        "inline": False,
                    },
                    {
                        "name": "💁‍♂️ Được tạo bởi",
                        "value": (
                            violation.creator.name if violation.creator else "Hệ thống"
                        ),
                        "inline": False,
                    },
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống nhắc nhở tự động"},
            }

            await self.discord_service.send_message_to_user(
                user_id=user.discord_id,
                content="",
                embed=embed,
            )
            logger.info(
                f"Sent violation notification to user {user.name} (ID: {user.discord_id})"
            )
        except Exception as e:
            logger.error(f"Failed to send violation notification: {e}")

    async def send_homework_assigned_notification(
        self, user: User, homework: Homework
    ) -> None:
        """Send a direct message to the user about a new homework assignment."""
        try:
            if not user or not user.discord_id:
                return

            # Format description for embed (limit length)
            description = homework.description
            if len(description) > 300:
                description = description[:297] + "..."

            embed = {
                "title": "📚 Bài tập mới đã được giao",
                "description": f"Chào **{user.name}**, bạn có một bài tập mới cần hoàn thành.",
                "color": 0x3498DB,  # Blue
                "fields": [
                    {"name": "📝 Tiêu đề", "value": homework.title, "inline": False},
                    {
                        "name": "⏰ Hạn nộp (Deadline)",
                        "value": homework.deadline.strftime("%H:%M %d/%m/%Y"),
                        "inline": False,
                    },
                    {
                        "name": "📖 Mô tả",
                        "value": description or "Không có mô tả",
                        "inline": False,
                    },
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống quản lý học tập"},
            }

            await self.discord_service.send_message_to_user(
                user_id=user.discord_id,
                content="",
                embed=embed,
            )
            logger.info(
                f"Sent homework notification to user {user.name} (ID: {user.discord_id})"
            )
        except Exception as e:
            logger.error(f"Failed to send homework notification: {e}")
