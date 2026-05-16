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
        self, user_id: str, content: str = "", embed: dict | None = None
    ) -> dict:
        """
        Send a direct message to a Discord user.

        Args:
            user_id: The Discord user ID to send the message to.
            content: The message content to send.
            embed: Optional embed dictionary for rich content.
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

                # Then, send the message to the DM channel
                send_message_url = f"{self.BASE_URL}/channels/{channel_id}/messages"
                from typing import Any

                message_payload: dict[str, Any] = {"content": content}

                if embed:
                    # Discord REST API expects an array of embeds
                    if "timestamp" not in embed:
                        from datetime import datetime

                        embed["timestamp"] = datetime.now(UTC).isoformat()
                    message_payload["embeds"] = [embed]

                async with session.post(
                    send_message_url, json=message_payload, headers=self.headers
                ) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to send message to user {user_id}: {error_text}"
                        )
                        raise DiscordServiceError(
                            f"Failed to send message: {error_text}",
                            status_code=response.status,
                        )

                    result = await response.json()
                    logger.info(f"Successfully sent message to user {user_id}")
                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Network error while sending message to user {user_id}: {e}")
            raise DiscordServiceError(f"Network error: {e}") from e

    async def send_message_to_room(
        self, channel_id: str, content: str = "", embed: dict | None = None
    ) -> dict:
        """
        Send a message to a Discord channel (room/text channel).

        Args:
            channel_id: The Discord channel ID to send the message to.
            content: The message content to send.
            embed: Optional embed dictionary for rich content.
        """
        from app.core.config import settings

        if settings.ENVIRONMENT != "production":
            logger.warning(
                f"Skipping Discord message to room {channel_id} (not in production)"
            )
            return {}

        try:
            async with aiohttp.ClientSession() as session:
                send_message_url = f"{self.BASE_URL}/channels/{channel_id}/messages"
                from typing import Any

                payload: dict[str, Any] = {"content": content}

                if embed:
                    # Discord REST API expects an array of embeds
                    if "timestamp" not in embed:
                        from datetime import datetime

                        embed["timestamp"] = datetime.now(UTC).isoformat()
                    payload["embeds"] = [embed]

                async with session.post(
                    send_message_url, json=payload, headers=self.headers
                ) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to send message to channel {channel_id}: {error_text}"
                        )
                        raise DiscordServiceError(
                            f"Failed to send message: {error_text}",
                            status_code=response.status,
                        )

                    result = await response.json()
                    logger.info(f"Successfully sent message to channel {channel_id}")
                    return result

        except aiohttp.ClientError as e:
            logger.error(
                f"Network error while sending message to channel {channel_id}: {e}"
            )
            raise DiscordServiceError(f"Network error: {e}") from e
