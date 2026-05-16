import base64
import hashlib
import random
import secrets
import string
import urllib.parse
from typing import Any

from loguru import logger

from app.core.config import settings
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.zalo.domain.entity import ZaloOAuthState, ZaloProfile
from app.zalo.domain.events import ZaloAccountBound, ZaloBotLinked
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient
from app.zalo.infrastructure.zalo_client import ZaloClient


class GetZaloLoginUrlUseCase:
    """Tạo URL đăng nhập Zalo sử dụng PKCE"""

    def execute(self) -> ZaloOAuthState:
        # 1. Tạo PKCE verifier và challenge
        code_verifier = secrets.token_urlsafe(32)

        # 2. Tính toán code_challenge
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

        callback_url = f"{settings.FRONTEND_HOST}/auth/zalo/callback"
        encoded_callback_url = urllib.parse.quote(callback_url, safe="")

        login_url = (
            f"https://oauth.zaloapp.com/v4/permission"
            f"?app_id={settings.ZALO_APP_ID}"
            f"&redirect_uri={encoded_callback_url}"
            f"&code_challenge={code_challenge}"
            f"&state={secrets.token_urlsafe(8)}"
        )

        return ZaloOAuthState(
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            login_url=login_url,
        )


class BindZaloAccountUseCase:
    """Giao dịch oauth_code lấy thông tin và liên kết tài khoản"""

    def __init__(
        self,
        zalo_client: ZaloClient,
        user_repo: Any,
        event_bus: type[EventBus] = EventBus,
    ):
        self.zalo_client = zalo_client
        self.user_repo = user_repo
        self.event_bus = event_bus

    async def execute(
        self, user_id: int, oauth_code: str, code_verifier: str
    ) -> ZaloProfile:
        try:
            # 1. Đổi code lấy access_token
            access_token = await self.zalo_client.get_access_token(
                oauth_code, code_verifier
            )

            # 2. Lấy thông tin cá nhân
            profile = await self.zalo_client.get_user_profile(access_token)

            # 3. Cập nhật User trong DB
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise BadRequestException("Không tìm thấy người dùng")

            user.zalo_id = profile.id
            self.user_repo.update(user)

            # 4. Phát sự kiện
            await self.event_bus.publish(
                ZaloAccountBound(
                    user_id=user_id, zalo_id=profile.id, zalo_name=profile.name
                )
            )

            return profile
        except Exception as e:
            if isinstance(e, BadRequestException):
                raise e
            logger.error(f"Lỗi khi liên kết Zalo: {e}")
            raise BadRequestException(f"Lỗi khi liên kết Zalo: {str(e)}")


class GenerateBotBindCodeUseCase:
    """Tạo mã liên kết bot (6 chữ số)"""

    def __init__(self, user_repo: Any):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> str:
        bind_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BadRequestException("Người dùng không tồn tại")

        user.zalo_bind_code = bind_code
        self.user_repo.update(user)

        return bind_code


class HandleBotWebhookUseCase:
    """Xử lý webhook từ Zalo Bot platform để liên kết tài khoản"""

    def __init__(
        self,
        bot_client: ZaloBotClient,
        user_repo: Any,
        event_bus: type[EventBus] = EventBus,
    ):
        self.bot_client = bot_client
        self.user_repo = user_repo
        self.event_bus = event_bus

    async def execute(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            logger.info(f"Nhận Zalo Bot webhook: {body}")

            event_name = body.get("event_name", "")
            sender_id = None
            text = None

            if event_name in ["user_send_text", "message.text.received"]:
                if "sender" in body and isinstance(body["sender"], dict):
                    sender_id = body["sender"].get("id")
                if "message" in body and isinstance(body["message"], dict):
                    text = body["message"].get("text")

            if sender_id and text:
                bind_code = text.strip().upper()
                user = self.user_repo.get_by_zalo_bind_code(bind_code)

                if user:
                    user.zalo_bot_id = str(sender_id)
                    user.zalo_bind_code = None
                    self.user_repo.update(user)

                    await self.bot_client.send_message(
                        chat_id=sender_id,
                        text=f"✅ Liên kết thành công! Tài khoản {user.name} sẽ nhận thông báo tại đây.",
                    )

                    await self.event_bus.publish(
                        ZaloBotLinked(
                            user_id=user.id,
                            zalo_bot_id=str(sender_id),
                            user_name=user.name,
                        )
                    )
                    return {"status": "success", "message": "Bound successfully"}
                else:
                    await self.bot_client.send_message(
                        chat_id=sender_id,
                        text="❌ Mã liên kết không hợp lệ hoặc đã hết hạn.",
                    )

            return {"status": "received"}
        except Exception as e:
            logger.error(f"Lỗi xử lý Zalo Webhook: {e}")
            return {"error": str(e)}


class SendZaloNotificationUseCase:
    """Gửi thông báo qua Zalo (OA hoặc Bot)"""

    def __init__(self, zalo_client: ZaloClient, bot_client: ZaloBotClient):
        self.zalo_client = zalo_client
        self.bot_client = bot_client

    async def execute(self, zalo_id: str | None, zalo_bot_id: str | None, text: str):
        if zalo_bot_id:
            await self.bot_client.send_message(zalo_bot_id, text)
            return

        if zalo_id:
            await self.zalo_client.send_oa_message(zalo_id, text)
