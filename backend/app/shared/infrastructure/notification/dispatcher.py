"""
Unified Notification Dispatcher.
Central notification hub that orchestrates In-App persistence and
asynchronous fault-isolated dispatch across Discord, Zalo, and Web Push.
"""

import asyncio
from typing import Any

from loguru import logger

from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    NotificationChannel,
)
from app.shared.infrastructure.notification.discord_channel import (
    DiscordNotificationChannel,
)
from app.shared.infrastructure.notification.in_app_channel import (
    InAppNotificationChannel,
)
from app.shared.infrastructure.notification.web_push_channel import (
    WebPushNotificationChannel,
)
from app.shared.infrastructure.notification.zalo_channel import ZaloNotificationChannel
from app.shared.infrastructure.notification_payload import NotificationPayload
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository


class UnifiedNotificationDispatcher:
    """
    Cổng điều phối phát thông báo trung tâm cho toàn bộ hệ thống DUT AI Manager.
    Tự động:
    1. Lưu thông báo nội bộ vào In-App DB (bảng notifications).
    2. Chạy ngầm phân phối đa kênh (Discord, Zalo, Web Push) với Fault Isolation và Retry.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        in_app_channel: InAppNotificationChannel,
        discord_channel: DiscordNotificationChannel,
        zalo_channel: ZaloNotificationChannel,
        web_push_channel: WebPushNotificationChannel,
    ):
        self.user_repo = user_repo
        self.in_app_channel = in_app_channel
        self.discord_channel = discord_channel
        self.zalo_channel = zalo_channel
        self.web_push_channel = web_push_channel
        self._external_channels: list[NotificationChannel] = [
            self.discord_channel,
            self.zalo_channel,
            self.web_push_channel,
        ]

    async def dispatch(self, payload: NotificationPayload) -> dict[str, Any]:
        """
        Phát thông báo chuẩn: Lưu In-App DB ngay lập tức, sau đó chạy ngầm
        phát tán song song đến các kênh ngoại vi (Discord, Zalo, Web Push).
        """
        user = self.user_repo.get_by_id(payload.user_id)
        if not user:
            logger.warning(
                f"UnifiedNotificationDispatcher: User {payload.user_id} not found, skip dispatch"
            )
            return {"in_app": False, "queued": False}

        # 1. Luôn lưu In-App (DB) trước tiên để đảm bảo tính toàn vẹn dữ liệu
        in_app_res = await self.in_app_channel.send(user, payload)

        # 2. Phân phối bất đồng bộ ra bên ngoài để không chặn tiến trình gọi
        asyncio.create_task(self._dispatch_external_channels(user, payload))

        return {
            "in_app": in_app_res.success,
            "queued": True,
        }

    async def dispatch_now(
        self, payload: NotificationPayload
    ) -> dict[str, ChannelDeliveryResult]:
        """
        Phát thông báo đồng thời và chờ tất cả các kênh hoàn thành (hữu ích cho testing và CLI).
        """
        user = self.user_repo.get_by_id(payload.user_id)
        if not user:
            logger.warning(
                f"UnifiedNotificationDispatcher: User {payload.user_id} not found, skip dispatch"
            )
            return {}

        results: dict[str, ChannelDeliveryResult] = {}

        # 1. In-App
        in_app_res = await self.in_app_channel.send(user, payload)
        results["in_app"] = in_app_res

        # 2. External channels song song
        ext_results = await self._dispatch_external_channels(user, payload)
        results.update(ext_results)

        return results

    async def _dispatch_external_channels(
        self, user: UserEntity, payload: NotificationPayload
    ) -> dict[str, ChannelDeliveryResult]:
        """Thực hiện phát tin đa kênh bên ngoài với cơ chế cách ly lỗi (Fault Isolation)."""
        tasks = [channel.send(user, payload) for channel in self._external_channels]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[str, ChannelDeliveryResult] = {}
        for channel, res in zip(self._external_channels, raw_results):
            ch_name = channel.channel_type.value
            if isinstance(res, Exception):
                logger.error(
                    f"UnifiedNotificationDispatcher: Channel {ch_name} failed with unhandled error: {res}"
                )
                results[ch_name] = ChannelDeliveryResult(
                    channel=channel.channel_type,
                    success=False,
                    status="FAILED",
                    error_message=str(res),
                )
            elif isinstance(res, ChannelDeliveryResult):
                results[ch_name] = res

        return results

    async def dispatch_room(
        self,
        room_id: str,
        payload: NotificationPayload,
    ) -> ChannelDeliveryResult:
        """Phát thông báo vào Room / Kênh Discord quản trị chung."""
        return await self.discord_channel.send_room(room_id, payload)
