import asyncio

from loguru import logger

from app.core.config import settings
from app.duty.domain.entity import DutyStatus
from app.duty.infrastructure.repository import DutyRepository
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.domain.events import (
    MeetingParticipantTransferred,
    PermissionRequestCreated,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.user.infrastructure.repository import UserRepository


class PermissionRequestNotificationHandler(EventHandler[PermissionRequestCreated]):
    """Xử lý gửi thông báo vào room Discord/Zalo khi có yêu cầu xin phép mới."""

    def __init__(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        user_repo: UserRepository,
    ):
        self.dispatcher = dispatcher
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
                content=f"Thành viên {user.name} vừa nộp 01 đơn xin phép loại {category_text}.",
                category=NotificationCategory.PERMISSION_REQUEST,
                level=NotificationLevel.WARNING,
                image_asset="anh-nhac-em-meme-9.webp",
                fields=fields,
            )

            await self.dispatcher.dispatch_room(
                room_id=room_id,
                payload=payload,
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
        dispatcher: UnifiedNotificationDispatcher,
        user_repo: UserRepository,
        meeting_repo: MeetingRepository,
        duty_repo: DutyRepository | None = None,
    ):
        self.dispatcher = dispatcher
        self.user_repo = user_repo
        self.meeting_repo = meeting_repo
        self.duty_repo = duty_repo

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

            # Kiểm tra xem buổi sinh hoạt mới có ca trực nhật không
            active_duties = []
            duty_team_name = ""
            if self.duty_repo and new_meeting.id:
                duties = self.duty_repo.get_by_meeting_id(new_meeting.id)
                active_duties = [
                    d
                    for d in duties
                    if d.status in (DutyStatus.PENDING, DutyStatus.AWAITING_APPROVAL)
                ]
                if active_duties:
                    duty_team_name = ", ".join(
                        d.team_name or "Nhóm trực" for d in active_duties if d.team_name
                    )

            fields = [
                {"name": "🔄 Ca cũ", "value": old_title, "inline": False},
                {
                    "name": "🎯 Ca mới",
                    "value": f"{new_meeting.title} ({new_time_str})",
                    "inline": False,
                },
            ]
            if active_duties:
                fields.append(
                    {
                        "name": "🧹 Lịch trực nhật phòng Lab",
                        "value": f"Buổi này có phân công trực nhật phòng Lab ({duty_team_name or 'Theo phân công'}). Bạn cùng tham gia trực nhật với nhóm nhé!",
                        "inline": False,
                    }
                )

            # 1. Gửi thông báo xác nhận cho cá nhân học viên
            user_payload = NotificationPayload(
                user_id=event.user_id,
                title="✅ XÁC NHẬN ĐỔI CA SINH HOẠT THÀNH CÔNG",
                content=(
                    f"Chào {user.name}, bạn đã đổi ca sinh hoạt thành công sang {new_meeting.title} "
                    f"diễn ra vào lúc {new_time_str}."
                ),
                category=NotificationCategory.MEETING,
                level=NotificationLevel.SUCCESS,
                fields=fields,
            )
            await self.dispatcher.dispatch(user_payload)

            # 1b. Nếu có ca trực nhật, gửi thêm thông báo phân công trực nhật cho học viên
            if active_duties:
                duty_date_str = new_meeting.start_time.strftime("%d/%m/%Y")
                duty_payload = NotificationPayload(
                    user_id=event.user_id,
                    title="🧹 [TRỰC NHẬT] PHÂN CÔNG TRỰC NHẬT PHÒNG LAB",
                    content=(
                        f"Chào {user.name}!\n"
                        f"Buổi sinh hoạt mới của bạn ({new_meeting.title} - {new_time_str}) "
                        f"có lịch phân công trực nhật phòng Lab do {duty_team_name or 'Nhóm trực'} phụ trách.\n"
                        f"👉 Bạn cùng tham gia quét dọn phòng Lab và nộp ảnh minh chứng cùng nhóm nhé!"
                    ),
                    category=NotificationCategory.DUTY,
                    level=NotificationLevel.INFO,
                    image_asset="meme-lam-viec.webp",
                    fields=[
                        {
                            "name": "👥 Nhóm phụ trách",
                            "value": duty_team_name or "Theo phân công",
                            "inline": True,
                        },
                        {
                            "name": "📅 Ngày trực",
                            "value": duty_date_str,
                            "inline": True,
                        },
                        {
                            "name": "📌 Lưu ý",
                            "value": "Nộp ảnh minh chứng hoàn thành trước 22:00 cùng ngày để tránh bị phạt vi phạm.",
                            "inline": False,
                        },
                    ],
                    action_url=f"{settings.FRONTEND_URL}/dashboard/duties",
                )
                await self.dispatcher.dispatch(duty_payload)

            # 2. Gửi thông báo đến Room quản lý Discord / Zalo
            room_id = settings.DISCORD_PERMISSION_ROOM_ID
            if room_id:
                room_payload = NotificationPayload(
                    user_id=event.user_id,
                    title="🔄 BIẾN ĐỘNG SĨ SỐ: ĐỔI BUỔI SINH HOẠT",
                    content=(
                        f"Thành viên {user.name} vừa chuyển ca thành công:\n"
                        f"- Rút khỏi: {old_title}\n"
                        f"- Tham gia vào: {new_meeting.title} ({new_time_str})"
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
                await self.dispatcher.dispatch_room(
                    room_id=room_id, payload=room_payload
                )

        except Exception as e:
            logger.error(f"Error sending transferred background notifications: {e}")
