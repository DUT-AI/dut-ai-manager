import random
import string
from typing import Optional

import zalo_bot
from app.api.v1.services.user_service import UserService
from app.core.config import settings
from loguru import logger
from zalo_bot import Update


class ZaloBotService:
    """Service for interacting with Zalo Bot Platform API."""

    def __init__(self, user_service: UserService):
        self.bot_token = settings.ZALO_BOT_TOKEN
        self._user_service = user_service

        self.bot = zalo_bot.Bot(token=self.bot_token)

    async def send_message_to_user(self, chat_id: str, text: str) -> Optional[dict]:
        """Send a message to a Zalo user via Zalo Bot Platform."""
        if not self.bot:
            logger.warning("ZALO_BOT_TOKEN is not configured")
            return None

        try:
            async with self.bot:
                msg = await self.bot.send_message(chat_id, text)
                logger.info(f"Sent Zalo Bot message to user {chat_id}")
                return msg.to_dict() if hasattr(msg, "to_dict") else {}
        except Exception as e:
            logger.error(f"Error while sending Zalo Bot message: {e}")
            return None

    def generate_bind_code(self, current_user) -> str:
        """Generate a random 6-character bind code to link Zalo bot."""
        bind_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        current_user.zalo_bind_code = bind_code
        self._user_service.update_raw_user(current_user)
        return bind_code

    async def handle_webhook(self, body: dict) -> dict:
        """Process incoming webhook from Zalo Bot Server."""
        try:
            logger.info(f"Received Zalo Bot webhook: {body}")

            # Webhook Payload từ Zalo Bot hoặc test script
            # Format chuẩn webhook: {"event_name": "user_send_text", "sender": {"id": "123"}, "message": {"text": "TEXT"}}

            event_name = body.get("event_name", "")
            sender_id = None
            text = None

            if "sender" in body and isinstance(body["sender"], dict):
                sender_id = body["sender"].get("id")
            if "message" in body and isinstance(body["message"], dict):
                text = body["message"].get("text")

            if sender_id and text:
                bind_code = text.strip()

                # Find user by bind code via service
                user = self._user_service.get_by_zalo_bind_code(bind_code)

                if user:
                    user.zalo_bot_id = str(sender_id)
                    user.zalo_bind_code = None
                    self._user_service.update_raw_user(user)

                    await self.send_message_to_user(
                        chat_id=sender_id,
                        text=f"✅ Liên kết thành công! Tài khoản của bạn ({user.name}) sẽ nhận thông báo tại đây.",
                    )
                    logger.info(
                        f"Successfully bound user {user.id} to Zalo Bot chat_id {sender_id}"
                    )
                else:
                    await self.send_message_to_user(
                        chat_id=sender_id,
                        text="❌ Mã liên kết không hợp lệ hoặc đã hết hạn. Vui lòng lấy mã mới trên trang DUT AI Manager.",
                    )
            return {"message": "Webhook received"}
        except Exception as e:
            logger.error(f"Error processing Zalo Bot webhook: {e}")
            return {"error": str(e)}
