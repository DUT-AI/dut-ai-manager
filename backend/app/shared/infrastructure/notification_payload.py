from dataclasses import dataclass
from enum import Enum
from typing import Any


class NotificationCategory(str, Enum):
    BILLING = "billing"
    HOMEWORK = "homework"
    VIOLATION = "violation"
    BONUS_POINT = "bonus_point"
    MEETING = "meeting"
    PERMISSION_REQUEST = "permission_request"
    DUTY = "duty"
    SYSTEM = "system"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value.upper() == val_upper or member.name == val_upper:
                    return member
        return None


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    CRITICAL = "critical"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value.upper() == val_upper or member.name == val_upper:
                    return member
        return None


@dataclass(frozen=True)
class NotificationPayload:
    user_id: int
    title: str
    content: str
    category: NotificationCategory
    level: NotificationLevel = NotificationLevel.INFO
    image_asset: str | None = (
        None  # Tên file trong app/assets (ví dụ: 'meme-hoc-bai.webp')
    )
    image_url: str | None = None  # Custom image URL bên ngoài nếu có
    action_url: str | None = None  # Link điều hướng người dùng (Frontend URL)
    fields: list[dict[str, Any]] | None = None  # Danh sách cặp key-value hiển thị
    color_hex: int | None = None  # Màu viền Discord Embed
    metadata: dict[str, Any] | None = None  # Dữ liệu ngữ cảnh linh hoạt

    # Optional metadata cho các tác vụ nhắc việc (Scheduled Reminders)
    task_type: str | None = None
    task_id: int | None = None
    reminder_stage: str | None = None
