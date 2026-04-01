from typing import Any, Dict, Optional

import zalo_bot
from app.core.config import settings
from loguru import logger


class ZaloBotClient:
    """Client giao tiếp với Zalo Bot Platform"""

    def __init__(self):
        self.bot_token = settings.ZALO_BOT_TOKEN
        self.bot = zalo_bot.Bot(token=self.bot_token) if self.bot_token else None

    async def send_message(self, chat_id: str, text: str) -> Optional[Dict[str, Any]]:
        """Gửi tin nhắn qua Zalo Bot Platform"""
        bot = self.bot
        if not bot:
            logger.warning("ZALO_BOT_TOKEN chưa được cấu hình")
            return None

        try:
            async with bot:
                msg = await bot.send_message(chat_id, text)
                logger.debug(f"Đã gửi tin nhắn Zalo Bot tới {chat_id}")
                return msg.to_dict() if hasattr(msg, "to_dict") else {}
        except Exception as e:
            logger.error(f"Lỗi khi gửi tin nhắn Zalo Bot: {e}")
            return None
