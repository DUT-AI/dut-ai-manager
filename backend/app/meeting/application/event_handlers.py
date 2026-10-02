import asyncio
from datetime import datetime

from loguru import logger

from app.meeting.domain.events import (
    MeetingCreated,
    MeetingUpdated,
    ParticipantCheckedIn,
)
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.shared.infrastructure.notification_service import NotificationService
from app.user.infrastructure.repository import UserRepository


class MeetingNotificationHandler(EventHandler):
    """Xử lý gửi thông báo Discord và Zalo cho các sự kiện của Meeting."""

    def __init__(
        self,
        notification_service: NotificationService,
        user_repo: UserRepository,
    ):
        self.notification_service = notification_service
        self.user_repo = user_repo

    async def handle(
        self, event: ParticipantCheckedIn | MeetingCreated | MeetingUpdated
    ) -> None:
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
            logger.info(
                f"Handling ParticipantCheckedIn for user {event.user_id} in meeting {event.meeting_id}"
            )
            asyncio.create_task(self._send_check_in_notification_task(event))
        except Exception as e:
            logger.error(f"Error in MeetingNotificationHandler.handle_check_in: {e}")

    async def _send_check_in_notification_task(
        self, event: ParticipantCheckedIn
    ) -> None:
        """Hàm chạy ngầm gửi thông báo check-in."""
        try:
            check_in_time = event.check_in_at.strftime("%H:%M:%S ngày %d/%m/%Y")
            status_text = "🔴 Trễ" if event.is_late else "🟢 Đúng giờ"

            fields = [
                {"name": "⏰ Thời gian", "value": check_in_time, "inline": True},
                {"name": "📊 Trạng thái", "value": status_text, "inline": True},
            ]

            payload = NotificationPayload(
                user_id=event.user_id,
                title="✅ ĐIỂM DANH THÀNH CÔNG",
                content=(
                    f"Bạn vừa thực hiện điểm danh thành công tại buổi học/họp: **{event.meeting_title}**."
                ),
                category=NotificationCategory.MEETING,
                level=NotificationLevel.SUCCESS
                if not event.is_late
                else NotificationLevel.WARNING,
                image_asset="meme-lam-viec.webp",
                fields=fields,
            )

            await self.notification_service.send_to_user(payload)
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

            asyncio.create_task(
                self._send_meeting_notification_task(users, event, "NEW")
            )
        except Exception as e:
            logger.error(
                f"Error in MeetingNotificationHandler._handle_meeting_created: {e}"
            )

    async def _handle_meeting_updated(self, event: MeetingUpdated) -> None:
        """Thông báo cho tất cả người dùng khi thông tin buổi họp bị thay đổi."""
        try:
            logger.info(f"Handling MeetingUpdated for meeting {event.meeting_id}")
            users = self.user_repo.get_by_ids(event.user_ids)
            if not users:
                logger.warning(f"No users found for meeting {event.meeting_id}")
                return

            asyncio.create_task(
                self._send_meeting_notification_task(users, event, "UPDATE")
            )
        except Exception as e:
            logger.error(
                f"Error in MeetingNotificationHandler._handle_meeting_updated: {e}"
            )

    async def _send_meeting_notification_task(
        self, users, event: MeetingCreated | MeetingUpdated, type: str
    ) -> None:
        """Hàm chạy ngầm gửi thông báo họp (Tạo mới hoặc Cập nhật)."""
        try:
            try:
                start_dt = datetime.fromisoformat(event.start_time)
                end_dt = datetime.fromisoformat(event.end_time)
                time_range = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')} ngày {start_dt.strftime('%d/%m/%Y')}"
            except Exception:
                time_range = f"{event.start_time} - {event.end_time}"

            is_new = type == "NEW"
            title_prefix = (
                "📅 LỊCH SINH HOẠT MỚI" if is_new else "🔄 CẬP NHẬT LỊCH SINH HOẠT"
            )
            description = (
                f"Bạn có lịch sinh hoạt mới: **{event.title}**"
                if is_new
                else f"Thông tin buổi sinh hoạt **{event.title}** đã được cập nhật."
            )

            fields = [{"name": "⏰ Thời gian", "value": time_range, "inline": False}]
            image_asset = (
                "anh-nhac-em-meme-9.webp" if is_new else "meme-met-moi-lam-viec.jpg"
            )

            for user in users:
                assert user.id is not None
                payload = NotificationPayload(
                    user_id=user.id,
                    title=title_prefix,
                    content=(
                        f"Chào **{user.name}**!\n"
                        f"{description}\n"
                        f"Vui lòng kiểm tra và sắp xếp tham gia đúng giờ."
                    ),
                    category=NotificationCategory.MEETING,
                    level=NotificationLevel.INFO
                    if is_new
                    else NotificationLevel.WARNING,
                    image_asset=image_asset,
                    fields=fields,
                )
                await self.notification_service.send_to_user(payload)

            logger.info(
                f"Finished sending meeting {type} notifications for {event.meeting_id}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in meeting notification task: {e}")
