"""
Notification Channel Protocol and Delivery Result types.
Implements the Strategy/Adapter Pattern for Multi-Channel Notification Dispatch.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.shared.infrastructure.notification_payload import NotificationPayload
from app.user.domain.entity import UserEntity as User


class ChannelType(str, Enum):
    IN_APP = "in_app"
    DISCORD = "discord"
    ZALO = "zalo"
    WEB_PUSH = "web_push"


@dataclass(frozen=True)
class ChannelDeliveryResult:
    channel: ChannelType
    success: bool
    status: str
    error_message: str | None = None


class NotificationChannel(Protocol):
    """Protocol chuẩn hóa cho mọi kênh gửi thông báo."""

    @property
    def channel_type(self) -> ChannelType:
        """Tên định danh kênh."""
        ...

    async def send(
        self, user: User, payload: NotificationPayload
    ) -> ChannelDeliveryResult:
        """
        Thực hiện gửi thông báo đến người dùng qua kênh này.
        Đảm bảo không bao giờ ném unhandled exception ra ngoài.
        """
        ...
