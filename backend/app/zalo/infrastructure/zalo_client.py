from typing import Any, Dict, Optional

import aiohttp
from app.core.config import settings
from app.zalo.domain.entity import ZaloProfile
from loguru import logger


class ZaloClient:
    """Client giao tiếp với Zalo API (OAuth, Graph, Official Account)"""

    def __init__(self):
        self.oauth_url = "https://oauth.zaloapp.com/v4/access_token"
        self.graph_url = "https://graph.zalo.me/v2.0/me"
        self.oa_msg_url = "https://openapi.zalo.me/v3.0/oa/message/cs"

    async def get_access_token(self, oauth_code: str, code_verifier: str) -> str:
        """Đổi oauth_code lấy access_token"""
        headers = {
            "secret_key": settings.ZALO_APP_SECRET,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "app_id": settings.ZALO_APP_ID,
            "grant_type": "authorization_code",
            "code": oauth_code,
            "code_verifier": code_verifier,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.oauth_url, headers=headers, data=payload
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or "access_token" not in data:
                    error_msg = (
                        f"Lỗi lấy access token: {data.get('error_name', 'Unknown')}"
                    )
                    logger.error(error_msg)
                    raise Exception(error_msg)
                return data["access_token"]

    async def get_user_profile(self, access_token: str) -> ZaloProfile:
        """Lấy thông tin người dùng từ Zalo Graph API"""
        headers = {"access_token": access_token}
        params = {"fields": "id,name"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.graph_url, headers=headers, params=params
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or data.get("error"):
                    error_msg = f"Lỗi lấy profile: {data.get('message', 'Unknown')}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                return ZaloProfile(id=str(data["id"]), name=data.get("name", ""))

    async def send_oa_message(self, user_id: str, text: str) -> Dict[str, Any]:
        """Gửi tin nhắn qua Zalo Official Account"""
        if not settings.ZALO_OA_ACCESS_TOKEN:
            logger.warning("ZALO_OA_ACCESS_TOKEN chưa được cấu hình")
            return {"error": "Not configured"}

        headers = {
            "access_token": settings.ZALO_OA_ACCESS_TOKEN,
            "Content-Type": "application/json",
        }
        payload = {"recipient": {"user_id": user_id}, "message": {"text": text}}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.oa_msg_url, headers=headers, json=payload
            ) as resp:
                data = await resp.json()
                if resp.status != 200 or data.get("error") != 0:
                    logger.error(f"Gửi tin nhắn OA thất bại cho {user_id}: {data}")
                return data
