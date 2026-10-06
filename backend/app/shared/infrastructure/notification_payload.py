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


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    CRITICAL = "critical"


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

