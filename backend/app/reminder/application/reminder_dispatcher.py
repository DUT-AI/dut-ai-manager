"""
Reminder Dispatcher.
Orchestrates deadline reminders across all channels via UnifiedNotificationDispatcher.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger

from app.core.config import settings
from app.reminder.application.embed_builder import format_remaining_time
from app.reminder.domain.entity import (
    ReminderStage,
    ReminderStatus,
    TaskType,
)
from app.reminder.infrastructure.repository import NotificationRepository
from app.shared.infrastructure.notification_payload import (
    NotificationCategory as PayloadCategory,
)
from app.shared.infrastructure.notification_payload import (
    NotificationLevel as PayloadLevel,
)
from app.shared.infrastructure.notification_payload import (
    NotificationPayload,
)
from app.user.infrastructure.repository import UserRepository

if TYPE_CHECKING:
    from app.shared.infrastructure.notification.dispatcher import (
        UnifiedNotificationDispatcher,
    )


class ReminderDispatcher:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        user_repo: UserRepository,
        unified_dispatcher: UnifiedNotificationDispatcher,
    ):
        self.notification_repo = notification_repo
        self.user_repo = user_repo
        self.unified_dispatcher = unified_dispatcher

    async def dispatch(
        self,
        task_type: TaskType,
        task_id: int,
        task_title: str,
        user_id: int,
        deadline: datetime,
        stage: ReminderStage,
        action_url: str,
        now: datetime,
    ) -> ReminderStatus:
        """Gửi thông báo nhắc việc đa kênh đồng nhất (Discord, In-App DB, Zalo, Web Push) qua UnifiedNotificationDispatcher."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return ReminderStatus.FAILED

        hours_left = max(0.1, (deadline - now).total_seconds() / 3600.0)
        deadline_str = deadline.strftime("%d/%m/%Y %H:%M")
        time_left_str = format_remaining_time(hours_left)

        category_map = {
            TaskType.HOMEWORK: PayloadCategory.HOMEWORK,
            TaskType.DUTY: PayloadCategory.DUTY,
            TaskType.MEETING_EVALUATION: PayloadCategory.MEETING,
            TaskType.MEETING: PayloadCategory.MEETING,
        }
        category = category_map.get(task_type, PayloadCategory.SYSTEM)
        level = PayloadLevel.CRITICAL if stage.is_critical else PayloadLevel.WARNING

        is_urgent = stage in [
            ReminderStage.OFFSET_1H,
            ReminderStage.OFFSET_4H,
            ReminderStage.FIXED_1930,
            ReminderStage.FIXED_2200,
        ]
        color_hex = 0xE74C3C if is_urgent else 0xF39C12

        type_name = {
            TaskType.HOMEWORK: "Bài tập về nhà",
            TaskType.DUTY: "Trực nhật vệ sinh",
            TaskType.MEETING_EVALUATION: "Đánh giá cuộc họp",
            TaskType.MEETING: "Buổi họp / Sinh hoạt",
        }.get(task_type, "Nhiệm vụ")

        full_action_url = (
            f"{settings.FRONTEND_URL}{action_url}"
            if not action_url.startswith("http")
            else action_url
        )

        if task_type == TaskType.MEETING:
            prefix = "🚨 [CẢNH BÁO GẤP]" if is_urgent else "⏰ [NHẮC NHỞ LỊCH HỌP]"
            title = f"{prefix} Buổi họp / Sinh hoạt: {task_title}"
            content = (
                f"Chào bạn! Bạn có lịch tham gia buổi sinh hoạt **{task_title}** sắp diễn ra.\n\n"
                f"📅 **Thời gian bắt đầu**: `{deadline_str}` (Giờ VN - UTC+7)\n"
                f"⏳ **Thời gian còn lại**: **{time_left_str}**\n\n"
                f"⚠️ *Lưu ý: Vui lòng có mặt đúng giờ và hoàn tất điểm danh trước khi bắt đầu buổi sinh hoạt.*\n\n"
                f"👉 [**Bấm vào đây để xem chi tiết và điểm danh**]({full_action_url})"
            )
        else:
            prefix = "🚨 [CẢNH BÁO GẤP]" if is_urgent else "⏰ [NHẮC NHỞ HẠN CHÓT]"
            title = f"{prefix} {type_name}: {task_title}"
            content = (
                f"Chào bạn! Bạn có nhiệm vụ **{task_title}** sắp đến hạn nộp.\n\n"
                f"📅 **Hạn chót**: `{deadline_str}` (Giờ VN - UTC+7)\n"
                f"⏳ **Thời gian còn lại**: **{time_left_str}**\n\n"
                f"⚠️ *Lưu ý: Vui lòng hoàn thành và nộp trước thời hạn trên để tránh bị hệ thống tự động ghi nhận lỗi vi phạm (Violation) vào cuối ngày.*\n\n"
                f"👉 [**Bấm vào đây để nộp bài ngay**]({full_action_url})"
            )

        payload = NotificationPayload(
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            level=level,
            action_url=full_action_url,
            color_hex=color_hex,
            task_type=task_type.value,
            task_id=task_id,
            reminder_stage=stage.value,
            metadata={
                "deadline_str": deadline_str,
                "time_left_str": time_left_str,
                "hours_left": hours_left,
            },
        )

        try:
            results = await self.unified_dispatcher.dispatch(payload)
        except Exception as e:
            logger.error(f"UnifiedNotificationDispatcher error for user {user_id}: {e}")
            return ReminderStatus.FAILED

        # Xác định trạng thái báo cáo dựa trên kết quả Discord (kênh DM chính)
        discord_res = results.get("discord")
        if discord_res:
            if discord_res.success:
                return ReminderStatus.SENT
            if discord_res.status == "NO_DISCORD_ID":
                return ReminderStatus.NO_DISCORD_ID
            if discord_res.status == "DM_BLOCKED":
                return ReminderStatus.DM_BLOCKED
            return ReminderStatus.FAILED

        # Fallback: Nếu không gửi discord (ví dụ không cấu hình discord channel), kiểm tra in_app
        in_app_res = results.get("in_app")
        if in_app_res and in_app_res.success:
            return ReminderStatus.SENT

        return ReminderStatus.FAILED
