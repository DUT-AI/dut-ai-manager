import asyncio
from datetime import datetime
from typing import cast
from loguru import logger
from app.core.discord_service import DiscordService
from app.meeting.domain.events import ParticipantCheckedIn, MeetingCreated, MeetingUpdated
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient
from app.shared.application.event_handler import EventHandler

class MeetingNotificationHandler(EventHandler):
    """Xử lý gửi thông báo Discord và Zalo cho các sự kiện của Meeting."""

    def __init__(
        self,
        discord_service: DiscordService,
        user_repo: UserRepository,
        zalo_bot: ZaloBotClient,
    ):
        self.discord_service = discord_service
        self.user_repo = user_repo
        self.zalo_bot = zalo_bot

    async def handle(self, event: ParticipantCheckedIn | MeetingCreated | MeetingUpdated) -> None:
        """EntryPoint cho EventBus, điều hướng tới các hàm xử lý cụ thể."""
        if isinstance(event, ParticipantCheckedIn):
            await self._handle_check_in(event)
        elif isinstance(event, MeetingCreated):
            await self._handle_meeting_created(event)
        elif isinstance(event, MeetingUpdated):
            await self._handle_meeting_updated(event)

    async def _handle_check_in(self, event: ParticipantCheckedIn) -> None:
        """Thông báo cho người dùng khi họ check-in thành công."""
        try:
            logger.info(f"Handling ParticipantCheckedIn for user {event.user_id} in meeting {event.meeting_id}")
            
            user = self.user_repo.get_by_id(event.user_id)
            if not user:
                logger.error(f"User {event.user_id} not found in check-in handler")
                return

            # Gửi thông báo trong background task
            asyncio.create_task(self._send_check_in_notification_task(user, event))
            
        except Exception as e:
            logger.error(f"Error in MeetingNotificationHandler.handle_check_in: {e}")

    async def _send_check_in_notification_task(self, user, event: ParticipantCheckedIn) -> None:
        """Hàm chạy ngầm gửi thông báo check-in."""
        try:
            check_in_time = event.check_in_at.strftime("%H:%M:%S ngày %d/%m/%Y")
            status_text = "🔴 Trễ" if event.is_late else "🟢 Đúng giờ"
            
            # 1. Discord Notification
            if user.discord_id and str(user.discord_id).isdigit():
                embed = {
                    "title": "✅ ĐIỂM DANH THÀNH CÔNG",
                    "description": f"Bạn vừa thực hiện điểm danh tại buổi họp: **{event.meeting_title}**",
                    "color": 0x2ECC71 if not event.is_late else 0xE74C3C,
                    "fields": [
                        {"name": "⏰ Thời gian", "value": check_in_time, "inline": True},
                        {"name": "📊 Trạng thái", "value": status_text, "inline": True},
                    ],
                    "footer": {"text": "DUT AI Manager • Hệ thống tự động"},
                }
                try:
                    await self.discord_service.send_message_to_user(
                        user_id=cast(str, user.discord_id),
                        content=f"Chào <@{user.discord_id}>! Bạn đã điểm danh thành công.",
                        embed=embed,
                    )
                except Exception as e:
                    logger.error(f"Background: Failed to send Discord check-in notification to {user.name}: {e}")

            # 2. Zalo Notification
            if user.zalo_bot_id:
                zalo_text = (
                    f"✅ ĐIỂM DANH THÀNH CÔNG\n\n"
                    f"Chào {user.name},\n"
                    f"Bạn vừa điểm danh thành công tại: {event.meeting_title}\n"
                    f"⏰ Thời gian: {check_in_time}\n"
                    f"📊 Trạng thái: {status_text}"
                )
                try:
                    await self.zalo_bot.send_message(
                        chat_id=user.zalo_bot_id, text=zalo_text
                    )
                    logger.info(f"Background: Sent Zalo check-in notification to {user.name}")
                except Exception as e:
                    logger.error(f"Background: Failed to send Zalo check-in notification to {user.name}: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in check-in notification task: {e}")

    async def _handle_meeting_created(self, event: MeetingCreated) -> None:
        """Thông báo cho tất cả người dùng khi có buổi họp mới được tạo."""
        try:
            logger.info(f"Handling MeetingCreated for meeting {event.meeting_id}")
            users = self.user_repo.get_by_ids(event.user_ids)
            if not users:
                logger.warning(f"No users found for meeting {event.meeting_id}")
                return

            asyncio.create_task(self._send_meeting_notification_task(users, event, "NEW"))
        except Exception as e:
            logger.error(f"Error in MeetingNotificationHandler._handle_meeting_created: {e}")

    async def _handle_meeting_updated(self, event: MeetingUpdated) -> None:
        """Thông báo cho tất cả người dùng khi thông tin buổi họp bị thay đổi."""
        try:
            logger.info(f"Handling MeetingUpdated for meeting {event.meeting_id}")
            users = self.user_repo.get_by_ids(event.user_ids)
            if not users:
                logger.warning(f"No users found for meeting {event.meeting_id}")
                return

            asyncio.create_task(self._send_meeting_notification_task(users, event, "UPDATE"))
        except Exception as e:
            logger.error(f"Error in MeetingNotificationHandler._handle_meeting_updated: {e}")

    async def _send_meeting_notification_task(self, users, event: MeetingCreated | MeetingUpdated, type: str) -> None:
        """Hàm chạy ngầm gửi thông báo họp (Tạo mới hoặc Cập nhật)."""
        try:
            # Parse thời gian (ISO string from event)
            try:
                start_dt = datetime.fromisoformat(event.start_time)
                end_dt = datetime.fromisoformat(event.end_time)
                time_range = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')} ngày {start_dt.strftime('%d/%m/%Y')}"
            except Exception:
                time_range = f"{event.start_time} - {event.end_time}"

            is_new = type == "NEW"
            title_prefix = "📅 LỊCH HỌP MỚI" if is_new else "🔄 CẬP NHẬT LỊCH HỌP"
            description = (
                f"Bạn có một lịch họp mới: **{event.title}**"
                if is_new
                else f"Thông tin buổi họp **{event.title}** đã được cập nhật."
            )
            color = 0x3498DB if is_new else 0xF1C40F # Blue for new, Yellow for update

            # 1. Discord Notification
            embed = {
                "title": title_prefix,
                "description": description,
                "color": color,
                "fields": [
                    {"name": "⏰ Thời gian", "value": time_range, "inline": False},
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống tự động"},
            }
            
            # 2. Zalo Notification Template
            zalo_text_template = (
                f"{title_prefix}\n\n"
                "Chào {user_name},\n"
                f"{description}\n"
                f"⏰ Thời gian: {time_range}\n"
                "Vui lòng kiểm tra website để xem chi tiết."
            )

            for user in users:
                # --- Discord ---
                if user.discord_id and str(user.discord_id).isdigit():
                    try:
                        await self.discord_service.send_message_to_user(
                            user_id=cast(str, user.discord_id),
                            content=f"Chào <@{user.discord_id}>! Bạn có lịch họp.",
                            embed=embed,
                        )
                    except Exception as e:
                        logger.error(f"Background: Failed to send Discord meeting notification to {user.name}: {e}")

                # --- Zalo ---
                if user.zalo_bot_id:
                    try:
                        zalo_text = zalo_text_template.format(user_name=user.name)
                        await self.zalo_bot.send_message(
                            chat_id=user.zalo_bot_id, text=zalo_text
                        )
                    except Exception as e:
                        logger.error(f"Background: Failed to send Zalo meeting notification to {user.name}: {e}")

            logger.info(f"Background: Finished sending meeting {type} notifications for {event.meeting_id}")

        except Exception as e:
            logger.error(f"Unexpected error in meeting notification task: {e}")
