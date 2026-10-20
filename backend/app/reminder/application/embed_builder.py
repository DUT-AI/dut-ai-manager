"""
Helper to build standardized Discord Rich Embed for task reminders.
"""

from datetime import UTC, datetime
from typing import Any

from app.reminder.domain.entity import NotificationLevel, ReminderStage, TaskType


def format_remaining_time(hours_left: float) -> str:
    """Định dạng thời gian còn lại sang chuỗi thân thiện với người dùng."""
    if hours_left <= 0:
        return "Đã quá hạn!"
    total_minutes = int(hours_left * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 24:
        days = hours // 24
        rem_hours = hours % 24
        return f"{days} ngày {rem_hours} giờ"
    if hours > 0:
        return f"{hours} giờ {minutes} phút"
    return f"{minutes} phút"


def build_reminder_embed(
    task_type: TaskType,
    task_title: str,
    deadline_str: str,
    hours_left: float,
    stage: ReminderStage,
    action_url: str,
) -> dict[str, Any]:
    """Tạo cấu trúc Discord Rich Embed chuẩn hóa."""
    is_urgent = stage in [
        ReminderStage.OFFSET_1H,
        ReminderStage.OFFSET_4H,
        ReminderStage.FIXED_1930,
        ReminderStage.FIXED_2200,
    ]
    color = 0xE74C3C if is_urgent else 0xF39C12  # Đỏ khẩn cấp hoặc Cam cảnh báo

    type_name = {
        TaskType.HOMEWORK: "Bài tập về nhà",
        TaskType.DUTY: "Trực nhật vệ sinh",
        TaskType.MEETING_EVALUATION: "Đánh giá cuộc họp",
    }.get(task_type, "Nhiệm vụ")

    prefix = "🚨 [CẢNH BÁO GẤP]" if is_urgent else "⏰ [NHẮC NHỞ HẠN CHÓT]"
    title = f"{prefix} {type_name}: {task_title}"

    time_left_str = format_remaining_time(hours_left)

    description = (
        f"Chào bạn! Bạn có nhiệm vụ **{task_title}** sắp đến hạn nộp.\n\n"
        f"📅 **Hạn chót**: `{deadline_str}` (Giờ VN - UTC+7)\n"
        f"⏳ **Thời gian còn lại**: **{time_left_str}**\n\n"
        f"⚠️ *Lưu ý: Vui lòng hoàn thành và nộp trước thời hạn trên để tránh bị hệ thống tự động ghi nhận lỗi vi phạm (Violation) vào cuối ngày.*\n\n"
        f"👉 [**Bấm vào đây để nộp bài ngay**]({action_url})"
    )

    return {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(UTC).isoformat(),
        "footer": {
            "text": "DUT AI Manager • Hệ thống tự động nhắc việc",
        },
    }
