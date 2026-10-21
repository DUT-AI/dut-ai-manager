"""
Reminder & In-App Notification Domain Entities & Value Objects.
Pure Pydantic models with zero framework / ORM dependencies.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from app.shared.domain.base_entity import BaseEntity


class TaskType(str, Enum):
    HOMEWORK = "HOMEWORK"
    DUTY = "DUTY"
    MEETING_EVALUATION = "MEETING_EVALUATION"


class NotificationCategory(str, Enum):
    HOMEWORK = "HOMEWORK"
    DUTY = "DUTY"
    MEETING = "MEETING"
    SYSTEM = "SYSTEM"


class NotificationLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ReminderStage(str, Enum):
    OFFSET_2D = "OFFSET_2D"
    OFFSET_1D = "OFFSET_1D"
    OFFSET_12H = "OFFSET_12H"
    OFFSET_4H = "OFFSET_4H"
    OFFSET_1H = "OFFSET_1H"
    FIXED_0800 = "FIXED_0800"
    FIXED_1200 = "FIXED_1200"
    FIXED_1930 = "FIXED_1930"
    FIXED_2200 = "FIXED_2200"

    @property
    def is_critical(self) -> bool:
        """Kiểm tra mốc nhắc nhở có thuộc nhóm khẩn cấp cao không."""
        return self in (ReminderStage.OFFSET_1H, ReminderStage.FIXED_2200)

    @classmethod
    def calculate_matching_stages(cls, deadline: datetime, now: datetime) -> list["ReminderStage"]:
        """Xác định danh sách các mốc ReminderStage phù hợp với thời điểm hiện tại và deadline."""
        stages: list[ReminderStage] = []

        # 1. Khung giờ cố định trong ngày (+/- 20 phút của khung giờ)
        hour = now.hour
        minute = now.minute

        # 08:00 (7:45 - 8:20)
        if (hour == 8 and minute <= 20) or (hour == 7 and minute >= 45):
            stages.append(cls.FIXED_0800)
        # 12:00 (11:45 - 12:20)
        if (hour == 12 and minute <= 20) or (hour == 11 and minute >= 45):
            stages.append(cls.FIXED_1200)
        # 19:30 (19:15 - 19:45)
        if hour == 19 and 15 <= minute <= 45:
            stages.append(cls.FIXED_1930)
        # 22:00 (21:45 - 22:20)
        if (hour == 22 and minute <= 20) or (hour == 21 and minute >= 45):
            stages.append(cls.FIXED_2200)

        # 2. Mốc đếm ngược động theo deadline
        diff_hours = (deadline - now).total_seconds() / 3600.0

        if 46.0 <= diff_hours <= 50.0:
            stages.append(cls.OFFSET_2D)
        elif 22.0 <= diff_hours <= 26.0:
            stages.append(cls.OFFSET_1D)
        elif 11.0 <= diff_hours <= 13.0:
            stages.append(cls.OFFSET_12H)
        elif 3.5 <= diff_hours <= 4.5:
            stages.append(cls.OFFSET_4H)
        elif 0.5 <= diff_hours <= 1.5:
            stages.append(cls.OFFSET_1H)

        return stages


class ReminderStatus(str, Enum):
    SENT = "SENT"
    FAILED = "FAILED"
    DM_BLOCKED = "DM_BLOCKED"
    NO_DISCORD_ID = "NO_DISCORD_ID"


class Notification(BaseEntity):
    id: int | None = None
    user_id: int
    title: str
    content: str
    category: NotificationCategory = NotificationCategory.SYSTEM
    level: NotificationLevel = NotificationLevel.INFO
    action_url: str | None = None
    is_read: bool = False
    read_at: datetime | None = None

    # Technical metadata for Reminder Engine, deduplication & tracking
    task_type: TaskType | None = None
    task_id: int | None = None
    reminder_stage: ReminderStage | None = None
    discord_status: ReminderStatus | None = None
    error_message: str | None = None
    created_at: datetime | None = None

    def mark_read(self, read_at: datetime) -> None:
        """Domain behavior: Đánh dấu thông báo là đã đọc."""
        self.is_read = True
        self.read_at = read_at

    @staticmethod
    def is_within_cooldown(
        last_sent_at: datetime | None,
        now: datetime,
        stage: ReminderStage,
        cooldown_hours: float = 3.0,
    ) -> bool:
        """Kiểm tra thời điểm gửi gần nhất có đang trong thời gian giãn cách (cooldown) không."""
        if not last_sent_at:
            return False
        # Mốc khẩn cấp 1H luôn được phép gửi, không áp dụng cooldown
        if stage == ReminderStage.OFFSET_1H:
            return False
        return (now - last_sent_at).total_seconds() < cooldown_hours * 3600

    @classmethod
    def create_deadline_reminder(
        cls,
        user_id: int,
        task_type: TaskType,
        task_id: int,
        task_title: str,
        deadline_str: str,
        time_left_str: str,
        stage: ReminderStage,
        action_url: str,
        now: datetime,
        discord_status: ReminderStatus | None = None,
        error_message: str | None = None,
    ) -> "Notification":
        """Factory method tạo thông báo nhắc nhở hạn chót thống nhất."""
        category_map = {
            TaskType.HOMEWORK: NotificationCategory.HOMEWORK,
            TaskType.DUTY: NotificationCategory.DUTY,
            TaskType.MEETING_EVALUATION: NotificationCategory.MEETING,
        }
        level = (
            NotificationLevel.CRITICAL
            if stage.is_critical
            else NotificationLevel.WARNING
        )
        return cls(
            user_id=user_id,
            title=f"Nhắc nhở hạn chót: {task_title}",
            content=(
                f"Nhiệm vụ {task_title} có hạn chót lúc {deadline_str} "
                f"(còn lại {time_left_str}). Vui lòng hoàn thành để tránh vi phạm."
            ),
            category=category_map.get(task_type, NotificationCategory.SYSTEM),
            level=level,
            action_url=action_url,
            is_read=False,
            task_type=task_type,
            task_id=task_id,
            reminder_stage=stage,
            discord_status=discord_status,
            error_message=error_message,
            created_at=now,
        )


class PushSubscription(BaseEntity):
    """
    Domain Entity biểu diễn một đăng ký thiết bị nhận thông báo đẩy Web Push (VAPID RFC 8292).
    """
    user_id: int
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = None
    is_active: bool = True
    last_used_at: datetime | None = None

