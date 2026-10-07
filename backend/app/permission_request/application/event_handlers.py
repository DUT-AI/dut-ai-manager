import asyncio

from loguru import logger

from app.core.config import settings
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.domain.events import (
    MeetingParticipantTransferred,
    PermissionRequestCreated,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.shared.infrastructure.notification_service import NotificationService
from app.user.infrastructure.repository import UserRepository


class PermissionRequestNotificationHandler(EventHandler[PermissionRequestCreated]):
    """Xử lý gửi thông báo vào room Discord/Zalo khi có yêu cầu xin phép mới."""

    def __init__(
        self,
        notification_service: NotificationService,
        user_repo: UserRepository,
    ):
        self.notification_service = notification_service
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
                case RequestCategory.CHANGE_MEETING:
                    category_text = "Đổi buổi sinh hoạt"
                case RequestCategory.OTHER:
                    category_text = "Khác"
                case _:
                    category_text = "Không xác định"

            fields = [
                {"name": "👤 Người yêu cầu", "value": user.name, "inline": True},
            ]

            if event.start_time:
                time_str = event.start_time.strftime("%d/%m/%Y %H:%M")
                fields.append(
                    {"name": "⏰ Thời gian/Hạn", "value": time_str, "inline": True}
                )

            fields.append(
                {
                    "name": "📝 Lý do",
                    "value": event.note or "Không có lý do cụ thể",
                    "inline": False,
                }
            )

            payload = NotificationPayload(
                user_id=event.user_id,
                title=f"📋 ĐƠN XIN PHÉP MỚI: {category_text.upper()}",
                content=f"Thành viên **{user.name}** vừa nộp 01 đơn xin phép loại **{category_text}**.",
                category=NotificationCategory.PERMISSION_REQUEST,
                level=NotificationLevel.WARNING,
                image_asset="anh-nhac-em-meme-9.webp",
                fields=fields,
            )

            await self.notification_service.send_to_room(
                room_id=room_id,
                payload=payload,
                channel="discord",
            )
            logger.info(
                f"Sent Discord room notification for permission request {event.request_id}"
            )

        except Exception as e:
            logger.error(
                f"Unexpected error in background permission notification task: {e}"
            )


class MeetingParticipantTransferredNotificationHandler(
    EventHandler[MeetingParticipantTransferred]
):
    """
    Xử lý gửi thông báo đa kênh khi học viên đổi buổi sinh hoạt thành công:
    1. Gửi tin nhắn xác nhận ca học mới cho cá nhân thành viên qua Zalo Bot / Discord DM.
    2. Gửi tin nhắn thông báo biến động danh sách sĩ số tới room quản lý.
    """

    def __init__(
        self,
        notification_service: NotificationService,
        user_repo: UserRepository,
        meeting_repo: MeetingRepository,
    ):
        self.notification_service = notification_service
        self.user_repo = user_repo
        self.meeting_repo = meeting_repo

    async def handle(self, event: MeetingParticipantTransferred) -> None:
        try:
            logger.info(
                f"Handling MeetingParticipantTransferred notification: User {event.user_id} -> Meeting {event.new_meeting_id}"
            )
            user = self.user_repo.get_by_id(event.user_id)
            if not user:
                return

            new_meeting = self.meeting_repo.get_by_id(event.new_meeting_id)
            if not new_meeting:
                return

            old_meeting = (
                self.meeting_repo.get_by_id(event.old_meeting_id)
                if event.old_meeting_id
                else None
            )

            asyncio.create_task(
                self._send_transferred_notifications(
                    event, user, old_meeting, new_meeting
                )
            )
        except Exception as e:
            logger.error(
                f"Error in MeetingParticipantTransferredNotificationHandler: {e}"
            )

    async def _send_transferred_notifications(
        self,
        event: MeetingParticipantTransferred,
        user,
        old_meeting,
        new_meeting,
    ) -> None:
        try:
            time_format = "%d/%m/%Y %H:%M"
            new_time_str = new_meeting.start_time.strftime(time_format)
            old_title = (
                f"{old_meeting.title} ({old_meeting.start_time.strftime(time_format)})"
                if old_meeting
                else "Chưa có buổi học (Đăng ký mới)"
            )

            # 1. Gửi thông báo xác nhận cho cá nhân học viên
            user_payload = NotificationPayload(
                user_id=event.user_id,
                title="✅ XÁC NHẬN ĐỔI CA SINH HOẠT THÀNH CÔNG",
                content=(
                    f"Chào **{user.name}**, bạn đã đổi ca sinh hoạt thành công sang **{new_meeting.title}** "
                    f"diễn ra vào lúc **{new_time_str}**."
                ),
                category=NotificationCategory.MEETING,
                level=NotificationLevel.SUCCESS,
                fields=[
                    {"name": "🔄 Ca cũ", "value": old_title, "inline": False},
                    {
                        "name": "🎯 Ca mới",
                        "value": f"{new_meeting.title} ({new_time_str})",
                        "inline": False,
                    },
                ],
            )
            await self.notification_service.send_to_user(user_payload)

            # 2. Gửi thông báo đến Room quản lý Discord / Zalo
            room_id = settings.DISCORD_PERMISSION_ROOM_ID
            if room_id:
                room_payload = NotificationPayload(
                    user_id=event.user_id,
                    title="🔄 BIẾN ĐỘNG SĨ SỐ: ĐỔI BUỔI SINH HOẠT",
                    content=(
                        f"Thành viên **{user.name}** vừa chuyển ca thành công:\n"
                        f"- **Rút khỏi**: {old_title}\n"
                        f"- **Tham gia vào**: {new_meeting.title} ({new_time_str})"
                    ),
                    category=NotificationCategory.MEETING,
                    level=NotificationLevel.INFO,
                    fields=[
                        {"name": "👤 Học viên", "value": user.name, "inline": True},
                        {
                            "name": "📝 Ghi chú",
                            "value": event.note or "Không có ghi chú",
                            "inline": True,
                        },
                    ],
                )
                await self.notification_service.send_to_room(
                    room_id=room_id, payload=room_payload, channel="discord"
                )

        except Exception as e:
            logger.error(
                f"Error sending transferred background notifications: {e}"
            )
