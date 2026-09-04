from typing import Any

import zalo_bot
from loguru import logger

from app.core.config import settings


class ZaloBotClient:
    """Client giao tiếp với Zalo Bot Platform"""

    def __init__(self):
        self.bot = None
        if settings.ZALO_BOT_TOKEN:
            try:
                self.bot = zalo_bot.Bot(token=settings.ZALO_BOT_TOKEN)
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Zalo Bot client: {e}")

    async def send_message(self, chat_id: str, text: str) -> dict[str, Any] | None:
        if not self.bot:
            logger.warning(f"Zalo Bot client chưa được cấu hình token, bỏ qua gửi tin tới {chat_id}")
            return None
        try:
            async with self.bot:
                msg = await self.bot.send_message(chat_id, text)
                logger.debug(f"Đã gửi tin nhắn Zalo Bot tới {chat_id}")
                return msg.to_dict() if hasattr(msg, "to_dict") else {}
        except Exception as e:
            logger.error(f"Lỗi khi gửi tin nhắn Zalo Bot: {e}")
            return None

