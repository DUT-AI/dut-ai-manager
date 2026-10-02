"""Discord Bot Service for sending messages."""

from datetime import UTC
from typing import Optional

import aiohttp
from loguru import logger

from app.core.config import settings


class DiscordServiceError(Exception):
    """Custom exception for Discord service errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DiscordService:
    """Service for sending messages via Discord Bot API."""

    BASE_URL = "https://discord.com/api/v10"
    _instance: Optional["DiscordService"] = None

    def __new__(cls) -> "DiscordService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.bot_token = settings.DISCORD_BOT_TOKEN
        self.headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
        }

    async def send_message_to_user(
        self,
        user_id: str,
        content: str = "",
        embed: dict | None = None,
        file_path: str | None = None,
    ) -> dict:
        """
        Send a direct message to a Discord user.

        Args:
            user_id: The Discord user ID to send the message to.
            content: The message content to send.
            embed: Optional embed dictionary for rich content.
            file_path: Optional local file path to attach directly to Discord.
        """
        try:
            async with aiohttp.ClientSession() as session:
                # First, create a DM channel with the user
                create_dm_url = f"{self.BASE_URL}/users/@me/channels"
                payload = {"recipient_id": user_id}

                async with session.post(
                    create_dm_url, json=payload, headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to create DM channel with user {user_id}: {error_text}"
                        )
                        raise DiscordServiceError(
                            f"Failed to create DM channel: {error_text}",
                            status_code=response.status,
                        )

                    dm_channel = await response.json()
                    channel_id = dm_channel["id"]

                return await self._send_to_channel(
                    session=session,
                    channel_id=channel_id,
                    content=content,
                    embed=embed,
                    file_path=file_path,
                )

        except aiohttp.ClientError as e:
            logger.error(f"Network error while sending message to user {user_id}: {e}")
            raise DiscordServiceError(f"Network error: {e}") from e

    async def send_message_to_room(
        self,
        channel_id: str,
        content: str = "",
        embed: dict | None = None,
        file_path: str | None = None,
    ) -> dict:
        """
        Send a message to a Discord channel (room/text channel).

        Args:
            channel_id: The Discord channel ID to send the message to.
            content: The message content to send.
            embed: Optional embed dictionary for rich content.
            file_path: Optional local file path to attach directly to Discord.
        """
        try:
            async with aiohttp.ClientSession() as session:
                return await self._send_to_channel(
                    session=session,
                    channel_id=channel_id,
                    content=content,
                    embed=embed,
                    file_path=file_path,
                )
        except aiohttp.ClientError as e:
            logger.error(
                f"Network error while sending message to channel {channel_id}: {e}"
            )
            raise DiscordServiceError(f"Network error: {e}") from e

    async def _send_to_channel(
        self,
        session: aiohttp.ClientSession,
        channel_id: str,
        content: str = "",
        embed: dict | None = None,
        file_path: str | None = None,
    ) -> dict:
        """Helper to send message or multipart attachment to a channel."""
        import json
        from pathlib import Path
        from typing import Any

        send_message_url = f"{self.BASE_URL}/channels/{channel_id}/messages"
        message_payload: dict[str, Any] = {"content": content}

        if embed:
            if "timestamp" not in embed:
                embed["timestamp"] = datetime.now(UTC).isoformat()
            message_payload["embeds"] = [embed]

        if file_path and Path(file_path).is_file():
            data = aiohttp.FormData()
            data.add_field(
                "payload_json",
                json.dumps(message_payload),
                content_type="application/json",
            )
            data.add_field(
                "files[0]",
                open(file_path, "rb"),
                filename=Path(file_path).name,
            )
            headers = {"Authorization": f"Bot {self.bot_token}"}
            async with session.post(send_message_url, data=data, headers=headers) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(f"Failed to send multipart message to channel {channel_id}: {error_text}")
                    raise DiscordServiceError(f"Failed to send message: {error_text}", status_code=response.status)
                result = await response.json()
                logger.info(f"Successfully sent multipart message to channel {channel_id}")
                return result
        else:
            async with session.post(send_message_url, json=message_payload, headers=self.headers) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(f"Failed to send message to channel {channel_id}: {error_text}")
                    raise DiscordServiceError(f"Failed to send message: {error_text}", status_code=response.status)
                result = await response.json()
                logger.info(f"Successfully sent message to channel {channel_id}")
                return result
