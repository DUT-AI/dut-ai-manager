from typing import Optional

import aiohttp
from app.core.config import settings
from loguru import logger


class ZaloService:
    """Service for interacting with Zalo Official Account OpenAPI."""

    def __init__(self):
        self.base_url = "https://openapi.zalo.me/v3.0/oa/message/cs"

    async def send_message_to_user(self, user_id: str, text: str) -> Optional[dict]:
        """Send a message to a Zalo user via Zalo OA."""
        if not settings.ZALO_OA_ACCESS_TOKEN:
            logger.warning("ZALO_OA_ACCESS_TOKEN is not configured")
            return None

        headers = {
            "access_token": settings.ZALO_OA_ACCESS_TOKEN,
            "Content-Type": "application/json",
        }

        payload = {"recipient": {"user_id": user_id}, "message": {"text": text}}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, headers=headers, json=payload
                ) as response:
                    data = await response.json()
                    if response.status != 200 or data.get("error") != 0:
                        logger.error(
                            f"Failed to send Zalo message to {user_id}. Response: {data}"
                        )
                    else:
                        logger.info(f"Sent Zalo message to user {user_id}")
                    return data
        except Exception as e:
            logger.error(f"Error while sending Zalo message: {e}")
            return None
