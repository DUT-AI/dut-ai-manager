"""
Reminder & In-App Notification Domain Entities & Value Objects.
Pure Pydantic models with zero framework / ORM dependencies.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from app.shared.domain.base_entity import BaseEntity


class TaskType(StrEnum):
    HOMEWORK = "HOMEWORK"
    DUTY = "DUTY"
    MEETING_EVALUATION = "MEETING_EVALUATION"
    MEETING = "MEETING"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value.upper() == val_upper or member.name == val_upper:
                    return member
        return None


class NotificationCategory(StrEnum):
    HOMEWORK = "HOMEWORK"
    DUTY = "DUTY"
    MEETING = "MEETING"
    VIOLATION = "VIOLATION"
    BONUS_POINT = "BONUS_POINT"
    BILLING = "BILLING"
    PERMISSION_REQUEST = "PERMISSION_REQUEST"
    SYSTEM = "SYSTEM"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value.upper() == val_upper or member.name == val_upper:
                    return member
        return None


class NotificationLevel(StrEnum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value.upper() == val_upper or member.name == val_upper:
                    return member
        return None


class ReminderStage(StrEnum):
    # ================= Active Pure Countdown Stages =================
    OFFSET_1D = "OFFSET_1D"  # 24 giờ trước hạn chót (22h - 26h)
    OFFSET_4H = "OFFSET_4H"  # 4 giờ trước hạn chót (3.5h - 4.5h)
    OFFSET_1H = "OFFSET_1H"  # 1 giờ trước hạn chót (0.5h - 1.5h) - Critical

    # ================= Deprecated Legacy Stages =====================
    # Giữ lại để đảm bảo tương thích ngược (Backward Compatibility)
    # khi đọc dữ liệu lịch sử từ bảng `notifications` trong database.
    OFFSET_2D = "OFFSET_2D"
    OFFSET_12H = "OFFSET_12H"
    FIXED_0800 = "FIXED_0800"
    FIXED_1200 = "FIXED_1200"
    FIXED_1930 = "FIXED_1930"
    FIXED_2200 = "FIXED_2200"

    @property
    def is_critical(self) -> bool:
        """Kiểm tra mốc nhắc nhở có thuộc nhóm khẩn cấp cao không (Chỉ duy nhất mốc 1H)."""
        return self == ReminderStage.OFFSET_1H

    @classmethod
    def calculate_matching_stages(
        cls, deadline: datetime, now: datetime
    ) -> list["ReminderStage"]:
        """
        Xác định danh sách các mốc ReminderStage phù hợp thuần đếm ngược (Countdown Offsets).
        Đã loại bỏ toàn bộ 4 khung giờ cố định cũ (08:00, 12:00, 19:30, 22:00)
        và các mốc dư thừa (OFFSET_2D, OFFSET_12H).
        Chỉ giữ 3 mốc chuẩn:
        - OFFSET_1D: 24 giờ trước hạn chót (22.0h - 26.0h)
        - OFFSET_4H: 4 giờ trước hạn chót (3.5h - 4.5h)
        - OFFSET_1H: 1 giờ trước hạn chót (0.5h - 1.5h)
        """
        stages: list[ReminderStage] = []

        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")

        # Chuẩn hóa về UTC aware cho phép so sánh khoảng thời gian
        now_utc = (
            now if now.tzinfo is not None else now.replace(tzinfo=vn_tz).astimezone(UTC)
        )
        deadline_utc = (
            deadline
            if deadline.tzinfo is not None
            else deadline.replace(tzinfo=vn_tz).astimezone(UTC)
        )

        diff_hours = (deadline_utc - now_utc).total_seconds() / 3600.0

        # Thuần mốc đếm ngược theo deadline
        if 22.0 <= diff_hours <= 26.0:
            stages.append(cls.OFFSET_1D)
        elif 3.5 <= diff_hours <= 4.5:
            stages.append(cls.OFFSET_4H)
        elif 0.5 <= diff_hours <= 1.5:
            stages.append(cls.OFFSET_1H)

        return stages


class ReminderStatus(StrEnum):
    SENT = "SENT"
    FAILED = "FAILED"
    DM_BLOCKED = "DM_BLOCKED"
    NO_DISCORD_ID = "NO_DISCORD_ID"
    NO_ZALO_ID = "NO_ZALO_ID"
    NO_SUBSCRIPTION = "NO_SUBSCRIPTION"


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
    zalo_status: ReminderStatus | None = None
    web_push_status: ReminderStatus | None = None
    error_message: str | None = None
    metadata_json: dict[str, Any] | None = None
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
    def create_event(
        cls,
        user_id: int,
        title: str,
        content: str,
        category: NotificationCategory,
        level: NotificationLevel = NotificationLevel.INFO,
        action_url: str | None = None,
        metadata_json: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> "Notification":
        """Factory method tạo thông báo tức thời từ Domain Events."""
        return cls(
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            level=level,
            action_url=action_url,
            is_read=False,
            metadata_json=metadata_json,
            created_at=now,
        )

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
            TaskType.MEETING: NotificationCategory.MEETING,
        }
        level = (
            NotificationLevel.CRITICAL
            if stage.is_critical
            else NotificationLevel.WARNING
        )
        if task_type == TaskType.MEETING:
            title = f"Nhắc nhở cuộc họp sắp diễn ra: {task_title}"
            content = (
                f"Cuộc họp {task_title} sẽ bắt đầu lúc {deadline_str} "
                f"(còn lại {time_left_str}). Vui lòng chuẩn bị tham gia và điểm danh đúng giờ."
            )
        else:
            title = f"Nhắc nhở hạn chót: {task_title}"
            content = (
                f"Nhiệm vụ {task_title} có hạn chót lúc {deadline_str} "
                f"(còn lại {time_left_str}). Vui lòng hoàn thành để tránh vi phạm."
            )
        return cls(
            user_id=user_id,
            title=title,
            content=content,
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
