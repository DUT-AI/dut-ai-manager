from typing import Any

import zalo_bot
from loguru import logger

from app.core.config import settings


class ZaloBotClient:
    """Client giao tiếp với Zalo Bot Platform"""

    def __init__(self):

        self.bot = zalo_bot.Bot(token=settings.ZALO_BOT_TOKEN)

    async def send_message(self, chat_id: str, text: str) -> dict[str, Any] | None:
        try:
            async with self.bot:
                msg = await self.bot.send_message(chat_id, text)
                logger.debug(f"Đã gửi tin nhắn Zalo Bot tới {chat_id}")
                return msg.to_dict() if hasattr(msg, "to_dict") else {}
        except Exception as e:
            logger.error(f"Lỗi khi gửi tin nhắn Zalo Bot: {e}")
            return None
