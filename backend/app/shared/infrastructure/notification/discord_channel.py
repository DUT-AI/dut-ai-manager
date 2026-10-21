"""
Discord Notification Channel Adapter.
Sends rich embed direct messages to users via DiscordService with retry and meme asset support.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.shared.infrastructure.asset_helper import get_asset_path, get_asset_url
from app.shared.infrastructure.discord_service import DiscordService
from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    ChannelType,
    NotificationChannel,
)
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.user.domain.entity import UserEntity as User

DEFAULT_CATEGORY_COLORS: dict[NotificationCategory, int] = {
    NotificationCategory.BILLING: 0x9B59B6,  # Tím đậm
    NotificationCategory.HOMEWORK: 0x3498DB,  # Xanh dương
    NotificationCategory.VIOLATION: 0xE74C3C,  # Đỏ cảnh báo
    NotificationCategory.BONUS_POINT: 0xF1C40F,  # Vàng kim
    NotificationCategory.MEETING: 0x2980B9,  # Xanh nước biển
    NotificationCategory.PERMISSION_REQUEST: 0xE67E22,  # Cam
    NotificationCategory.DUTY: 0x1ABC9C,  # Xanh ngọc
    NotificationCategory.SYSTEM: 0x95A5A6,  # Xám bạc
}

LEVEL_COLORS: dict[NotificationLevel, int] = {
    NotificationLevel.INFO: 0x3498DB,
    NotificationLevel.SUCCESS: 0x2ECC71,
    NotificationLevel.WARNING: 0xE67E22,
    NotificationLevel.CRITICAL: 0xE74C3C,
}


class DiscordNotificationChannel(NotificationChannel):
    """Channel adapter gửi thông báo qua Discord bot."""

    def __init__(self, discord_service: DiscordService):
        self.discord_service = discord_service

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.DISCORD

    def _resolve_image_url(self, payload: NotificationPayload) -> str | None:
        """Xác định URL hình ảnh (ưu tiên custom image_url, sau đó đến image_asset từ assets)."""
        if payload.image_url:
            return payload.image_url
        if payload.image_asset:
            asset_path = get_asset_path(payload.image_asset)
            if asset_path:
                return f"attachment://{asset_path.name}"
            return get_asset_url(payload.image_asset)
        return None

    def _build_discord_embed(self, payload: NotificationPayload) -> dict[str, Any]:
        """Tạo cấu trúc Discord Rich Embed chuẩn hóa."""
        color = payload.color_hex
        if color is None:
            color = DEFAULT_CATEGORY_COLORS.get(
                payload.category, LEVEL_COLORS.get(payload.level, 0x3498DB)
            )

        embed: dict[str, Any] = {
            "title": payload.title,
            "description": payload.content,
            "color": color,
            "timestamp": datetime.now(UTC).isoformat(),
            "footer": {"text": "DUT AI Club • Notification"},
        }

        resolved_img = self._resolve_image_url(payload)
        if resolved_img:
            embed["image"] = {"url": resolved_img}

        if payload.action_url:
            embed["url"] = payload.action_url

        if payload.fields:
            embed["fields"] = [
                {
                    "name": f.get("name", ""),
                    "value": f.get("value", ""),
                    "inline": f.get("inline", True),
                }
                for f in payload.fields
            ]

        return embed

    async def send(
        self, user: User, payload: NotificationPayload
    ) -> ChannelDeliveryResult:
        if not user.discord_id:
            return ChannelDeliveryResult(
                channel=ChannelType.DISCORD,
                success=False,
                status="NO_DISCORD_ID",
            )

        embed = self._build_discord_embed(payload)
        file_path = (
            str(get_asset_path(payload.image_asset))
            if payload.image_asset and get_asset_path(payload.image_asset)
            else None
        )

        max_retries = 3
        last_error = None
        is_dm_blocked = False

        for attempt in range(1, max_retries + 1):
            try:
                await self.discord_service.send_message_to_user(
                    user_id=user.discord_id,
                    embed=embed,
                    file_path=file_path,
                )
                logger.info(
                    f"DiscordNotificationChannel: Sent message to user {user.id} (discord_id: {user.discord_id})"
                )
                return ChannelDeliveryResult(
                    channel=ChannelType.DISCORD,
                    success=True,
                    status="SENT",
                )
            except Exception as e:
                err_msg = str(e)
                last_error = err_msg
                if "50007" in err_msg or "Cannot send messages to this user" in err_msg:
                    is_dm_blocked = True
                    logger.warning(
                        f"DiscordNotificationChannel: DM blocked by user {user.id} ({user.discord_id})"
                    )
                    break
                logger.warning(
                    f"DiscordNotificationChannel: Attempt {attempt}/{max_retries} failed for user {user.id}: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)

        status = "DM_BLOCKED" if is_dm_blocked else "FAILED"
        return ChannelDeliveryResult(
            channel=ChannelType.DISCORD,
            success=False,
            status=status,
            error_message=last_error,
        )

    async def send_room(
        self,
        room_id: str,
        payload: NotificationPayload,
        max_retries: int = 3,
    ) -> ChannelDeliveryResult:
        """Gửi thông báo vào Room / Channel quản trị chung trên Discord."""
        embed = self._build_discord_embed(payload)
        file_path = (
            str(get_asset_path(payload.image_asset))
            if payload.image_asset and get_asset_path(payload.image_asset)
            else None
        )

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                await self.discord_service.send_message_to_room(
                    channel_id=room_id,
                    embed=embed,
                    file_path=file_path,
                )
                return ChannelDeliveryResult(
                    channel=ChannelType.DISCORD,
                    success=True,
                    status="SENT",
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"DiscordNotificationChannel: Room attempt {attempt}/{max_retries} failed for room {room_id}: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)

        return ChannelDeliveryResult(
            channel=ChannelType.DISCORD,
            success=False,
            status="FAILED",
            error_message=last_error,
        )
