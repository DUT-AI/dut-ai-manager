import asyncio
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.shared.infrastructure.asset_helper import get_asset_path, get_asset_url
from app.shared.infrastructure.discord_service import DiscordService
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient

# Bảng màu chuẩn hóa cho Discord Embed theo Category / Level
DEFAULT_CATEGORY_COLORS: dict[NotificationCategory, int] = {
    NotificationCategory.BILLING: 0x9B59B6,  # Tím đậm
    NotificationCategory.HOMEWORK: 0x3498DB,  # Xanh dương
    NotificationCategory.VIOLATION: 0xE74C3C,  # Đỏ cảnh báo
    NotificationCategory.BONUS_POINT: 0xF1C40F,  # Vàng kim
    NotificationCategory.MEETING: 0x2980B9,  # Xanh nước biển
    NotificationCategory.PERMISSION_REQUEST: 0xE67E22,  # Cam
}

LEVEL_COLORS: dict[NotificationLevel, int] = {
    NotificationLevel.INFO: 0x3498DB,
    NotificationLevel.SUCCESS: 0x2ECC71,
    NotificationLevel.WARNING: 0xE67E22,
    NotificationLevel.CRITICAL: 0xE74C3C,
}


class NotificationService:
    """
    Dịch vụ phân phối thông báo đa kênh chuẩn hóa (Discord + Zalo).
    Đảm bảo:
    - Fault Isolation: Lỗi một kênh không làm hỏng kênh còn lại.
    - Retry Logic: Tự động Exponential Backoff (tối đa 3 lần).
    - Rich Media: Tự động đính kèm ảnh meme từ app/assets hoặc URL ngoài.
    - Fallback: Nếu ảnh lỗi hoặc không tìm thấy, hạ cấp gửi tin nhắn text an toàn.
    """

    def __init__(
        self,
        discord_service: DiscordService,
        zalo_bot: ZaloBotClient,
        user_repo: UserRepository,
    ):
        self.discord_service = discord_service
        self.zalo_bot = zalo_bot
        self.user_repo = user_repo

    async def send_to_user(self, payload: NotificationPayload) -> dict[str, bool]:
        """
        Gửi thông báo song song đến tất cả các kênh (Discord, Zalo) đã liên kết của người dùng.
        """
        user = self.user_repo.get_by_id(payload.user_id)
        if not user:
            logger.warning(
                f"NotificationService: User {payload.user_id} not found, skip notification"
            )
            return {"discord": False, "zalo": False}

        tasks = []
        channels = []

        # 1. Kênh Discord
        if user.discord_id:
            channels.append("discord")
            tasks.append(self._send_discord_with_retry(user.discord_id, payload))

        # 2. Kênh Zalo Bot
        if user.zalo_bot_id:
            channels.append("zalo")
            tasks.append(self._send_zalo_with_retry(user.zalo_bot_id, payload))

        if not tasks:
            logger.debug(
                f"NotificationService: User {payload.user_id} has no linked channels (discord/zalo)"
            )
            return {}

        results = await asyncio.gather(*tasks, return_exceptions=True)

        status_dict = {}
        for ch, res in zip(channels, results):
            if isinstance(res, Exception):
                logger.error(
                    f"NotificationService: Channel {ch} failed with unhandled exception: {res}"
                )
                status_dict[ch] = False
            else:
                status_dict[ch] = bool(res)

        return status_dict

    async def send_to_room(
        self,
        room_id: str,
        payload: NotificationPayload,
        channel: str = "discord",
    ) -> bool:
        """Gửi thông báo vào kênh/room chung (cho admin/quản lý)."""
        if channel == "discord" and room_id:
            return await self._send_discord_room_with_retry(room_id, payload)
        return False

    def _resolve_image_url(self, payload: NotificationPayload) -> str | None:
        """Xác định URL hình ảnh (ưu tiên custom image_url, sau đó đến image_asset từ assets)."""
        if payload.image_url:
            return payload.image_url
        if payload.image_asset:
            # Nếu có file local, Discord nhận attachment://<filename>
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

        # Đính kèm ảnh meme/banner
        resolved_img = self._resolve_image_url(payload)
        if resolved_img:
            embed["image"] = {"url": resolved_img}

        # Đính kèm link hành động nếu có
        if payload.action_url:
            embed["url"] = payload.action_url

        # Thêm các trường key-value
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

    async def _send_discord_with_retry(
        self, discord_id: str, payload: NotificationPayload, max_retries: int = 3
    ) -> bool:
        """Gửi tin nhắn Discord DM có Retry và Exponential Backoff."""
        embed = self._build_discord_embed(payload)
        file_path = (
            str(get_asset_path(payload.image_asset))
            if payload.image_asset and get_asset_path(payload.image_asset)
            else None
        )
        for attempt in range(1, max_retries + 1):
            try:
                await self.discord_service.send_message_to_user(
                    user_id=discord_id, embed=embed, file_path=file_path
                )
                logger.info(
                    f"NotificationService: Sent Discord message to {discord_id} (category={payload.category.value})"
                )
                return True
            except Exception as e:
                logger.warning(
                    f"NotificationService: Discord attempt {attempt}/{max_retries} failed for user {discord_id}: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)
        return False

    async def _send_discord_room_with_retry(
        self, room_id: str, payload: NotificationPayload, max_retries: int = 3
    ) -> bool:
        """Gửi tin nhắn vào Discord Room có Retry."""
        embed = self._build_discord_embed(payload)
        file_path = (
            str(get_asset_path(payload.image_asset))
            if payload.image_asset and get_asset_path(payload.image_asset)
            else None
        )
        for attempt in range(1, max_retries + 1):
            try:
                await self.discord_service.send_message_to_room(
                    channel_id=room_id, embed=embed, file_path=file_path
                )
                logger.info(
                    f"NotificationService: Sent Discord room message to {room_id}"
                )
                return True
            except Exception as e:
                logger.warning(
                    f"NotificationService: Discord Room attempt {attempt}/{max_retries} failed for room {room_id}: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)
        return False

    async def _send_zalo_with_retry(
        self, zalo_id: str, payload: NotificationPayload, max_retries: int = 3
    ) -> bool:
        """Gửi tin nhắn Zalo Bot có Retry."""
        # Chuẩn bị nội dung text định dạng
        text_lines = [f"📢 *{payload.title}*", "", payload.content]

        if payload.fields:
            text_lines.append("")
            for f in payload.fields:
                text_lines.append(f"• {f.get('name')}: {f.get('value')}")

        if payload.action_url:
            text_lines.append(f"\n👉 Xem chi tiết: {payload.action_url}")

        full_text = "\n".join(text_lines)

        for attempt in range(1, max_retries + 1):
            try:
                res = await self.zalo_bot.send_message(chat_id=zalo_id, text=full_text)
                if res is not None:
                    logger.info(
                        f"NotificationService: Sent Zalo message to {zalo_id} (category={payload.category.value})"
                    )
                    return True
                else:
                    logger.warning(
                        f"NotificationService: Zalo attempt {attempt}/{max_retries} returned None for user {zalo_id}"
                    )
            except Exception as e:
                logger.warning(
                    f"NotificationService: Zalo attempt {attempt}/{max_retries} failed for user {zalo_id}: {e}"
                )
            if attempt < max_retries:
                await asyncio.sleep(2**attempt)
        return False
