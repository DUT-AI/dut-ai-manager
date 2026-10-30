"""
Zalo Bot Notification Channel Adapter.
Sends messages to users via ZaloBotClient with retry support.
"""

import asyncio

from loguru import logger

from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    ChannelType,
    NotificationChannel,
)
from app.shared.infrastructure.notification_payload import NotificationPayload
from app.user.domain.entity import UserEntity as User
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class ZaloNotificationChannel(NotificationChannel):
    """Channel adapter gửi thông báo qua Zalo Bot."""

    def __init__(self, zalo_bot: ZaloBotClient):
        self.zalo_bot = zalo_bot

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.ZALO

    async def send(
        self, user: User, payload: NotificationPayload
    ) -> ChannelDeliveryResult:
        if not user.zalo_bot_id:
            return ChannelDeliveryResult(
                channel=ChannelType.ZALO,
                success=False,
                status="NO_ZALO_ID",
            )

        text_lines = [f"{payload.title}", "", payload.content]

        if payload.fields:
            text_lines.append("")
            for f in payload.fields:
                text_lines.append(f"• {f.get('name')}: {f.get('value')}")

        if payload.action_url:
            text_lines.append(f"\n👉 Xem chi tiết: {payload.action_url}")

        full_text = "\n".join(text_lines)

        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                res = await self.zalo_bot.send_message(
                    chat_id=user.zalo_bot_id, text=full_text
                )
                if res is not None:
                    logger.info(
                        f"ZaloNotificationChannel: Sent message to user {user.id} (zalo_bot_id: {user.zalo_bot_id})"
                    )
                    return ChannelDeliveryResult(
                        channel=ChannelType.ZALO,
                        success=True,
                        status="SENT",
                    )
                else:
                    logger.warning(
                        f"ZaloNotificationChannel: Attempt {attempt}/{max_retries} returned None for user {user.id}"
                    )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"ZaloNotificationChannel: Attempt {attempt}/{max_retries} failed for user {user.id}: {e}"
                )
            if attempt < max_retries:
                await asyncio.sleep(2**attempt)

        return ChannelDeliveryResult(
            channel=ChannelType.ZALO,
            success=False,
            status="FAILED",
            error_message=last_error,
        )
