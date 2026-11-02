"""
Notification infrastructure module.
Provides Unified Notification Dispatcher and Multi-Channel Adapters.
"""

from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    ChannelType,
    DispatchResult,
    NotificationChannel,
)
from app.shared.infrastructure.notification.discord_channel import (
    DiscordNotificationChannel,
)
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification.in_app_channel import (
    InAppNotificationChannel,
)
from app.shared.infrastructure.notification.web_push_channel import (
    WebPushNotificationChannel,
)
from app.shared.infrastructure.notification.zalo_channel import ZaloNotificationChannel

__all__ = [
    "ChannelDeliveryResult",
    "ChannelType",
    "DispatchResult",
    "NotificationChannel",
    "InAppNotificationChannel",
    "DiscordNotificationChannel",
    "ZaloNotificationChannel",
    "WebPushNotificationChannel",
    "UnifiedNotificationDispatcher",
]
