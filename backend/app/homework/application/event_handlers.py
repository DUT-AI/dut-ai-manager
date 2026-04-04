import asyncio
from typing import cast
from app.core.discord_service import DiscordService
from app.homework.domain.value_objects import HomeworkAssigned
from app.homework.infrastructure.repository import HomeworkRepository
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient
from loguru import logger


class HomeworkNotificationHandler:
    """Xử lý gửi thông báo Discord và Zalo khi có bài tập mới."""

    def __init__(
        self,
        discord_service: DiscordService,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        zalo_bot: ZaloBotClient,
    ):
        self.discord_service = discord_service
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.zalo_bot = zalo_bot

    async def handle(self, event: HomeworkAssigned) -> None:
        """Thông báo cho người dùng trên Discord và Zalo khi họ được giao bài tập mới."""
        try:
            logger.info(f"Handling HomeworkAssigned for homework {event.homework_id}")
            homework = self.homework_repo.get_by_id(event.homework_id)
            if not homework:
                logger.error(f"Homework {event.homework_id} not found in handler")
                return

            users = self.user_repo.get_by_ids(event.assignee_ids)
            if not users:
                logger.warning(f"No users found for assignee_ids: {event.assignee_ids}")
                return

            asyncio.create_task(self._send_notifications_task(homework, users))
            logger.info(
                f"Notifications for homework {event.homework_id} have been scheduled in background"
            )

        except Exception as e:
            logger.error(f"Error in HomeworkNotificationHandler: {e}")

    async def _send_notifications_task(self, homework, users) -> None:
        """Hàm chạy ngầm để gửi thông báo qua Discord và Zalo."""
        try:
            deadline_str = homework.deadline.strftime("%H:%M ngày %d/%m/%Y")

            # 1. Chuẩn bị nội dung cho Discord (Embed)
            embed = {
                "title": "📚 BÀI TẬP MỚI ĐƯỢC GIAO",
                "description": f"Bạn vừa được giao bài tập mới: **{homework.title}**",
                "color": 0x3498DB,  # Blue
                "fields": [
                    {"name": "⏰ Hạn nộp", "value": deadline_str, "inline": True},
                    {
                        "name": "📋 Chi tiết",
                        "value": "Vui lòng kiểm tra trang chủ để xem chi tiết yêu cầu.",
                        "inline": False,
                    },
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống tự động"},
            }
            if homework.file_url:
                embed["fields"].append(
                    {
                        "name": "🔗 File đính kèm",
                        "value": f"[Tải về tài liệu]({homework.file_url})",
                        "inline": False,
                    }
                )

            # 2. Chuẩn bị nội dung cho Zalo (Text)
            zalo_text_template = (
                "📚 BÀI TẬP MỚI ĐƯỢC GIAO\n\n"
                "Chào {user_name},\n"
                "Bạn vừa được giao bài tập mới: {title}\n"
                "⏰ Hạn nộp: {deadline}\n"
                "Vui lòng kiểm tra website để xem chi tiết."
            )

            # 3. Gửi thông báo cho từng người
            for user in users:
                # --- Discord ---
                if user.discord_id:
                    try:
                        await self.discord_service.send_message_to_user(
                            user_id=cast(str, user.discord_id),
                            content=f"Chào <@{user.discord_id}>! Bạn có bài tập mới.",
                            embed=embed,
                        )
                    except Exception as e:
                        logger.error(
                            f"Background: Failed to send Discord notification to {user.name}: {e}"
                        )

                # --- Zalo (Bot) ---
                if user.zalo_bot_id:
                    try:
                        zalo_text = zalo_text_template.format(
                            user_name=user.name,
                            title=homework.title,
                            deadline=deadline_str,
                        )
                        await self.zalo_bot.send_message(
                            chat_id=user.zalo_bot_id, text=zalo_text
                        )
                        logger.info(
                            f"Background: Sent Zalo notification to {user.name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Background: Failed to send Zalo notification to {user.name}: {e}"
                        )

            logger.info(
                f"Background: Finished sending notifications for homework {homework.id}"
            )

        except Exception as e:
            logger.error(f"Unexpected error in background notification task: {e}")
