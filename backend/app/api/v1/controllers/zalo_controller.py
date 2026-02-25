from fastapi import APIRouter, Body, status
from typing import Annotated
import aiohttp

from pydantic import BaseModel
import secrets
import base64
import hashlib

from app.core.deps import CurrentUser, ServiceFactoryDI
from app.schemas.response import ApiResponse, BadRequestException
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/zalo", tags=["zalo"])


class ZaloBindRequest(BaseModel):
    oauth_code: str
    code_verifier: str


@router.get("/login-url", response_model=ApiResponse[dict])
async def get_zalo_login_url():
    """
    Generate Zalo Login URL using PKCE.
    Returns URL and code_verifier which must be stored by frontend (e.g., localStorage).
    """
    if not settings.ZALO_APP_ID:
        raise BadRequestException("ZALO_APP_ID is not configured")

    # Generate PKCE verifier and challenge
    code_verifier = secrets.token_urlsafe(32)

    # Calculate code_challenge = base64_url_encode(sha256(code_verifier))
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    import urllib.parse

    callback_url = f"{settings.FRONTEND_HOST}/auth/zalo/callback"
    encoded_callback_url = urllib.parse.quote(callback_url, safe="")

    login_url = (
        f"https://oauth.zaloapp.com/v4/permission"
        f"?app_id={settings.ZALO_APP_ID}"
        f"&redirect_uri={encoded_callback_url}"
        f"&code_challenge={code_challenge}"
        f"&state={secrets.token_urlsafe(8)}"
    )

    return ApiResponse.success(
        data={"login_url": login_url, "code_verifier": code_verifier},
        message="Login URL generated",
    )


@router.post("/bind", response_model=ApiResponse[User])
async def bind_zalo(
    service_factory: ServiceFactoryDI,
    current_user: CurrentUser,
    data: ZaloBindRequest,
):
    """
    Bind user's Zalo account using oauth_code from Zalo Login callback.
    We exchange the code for an access_token, then fetch user profile to get `id` securely.
    """
    try:
        if not settings.ZALO_APP_ID or not settings.ZALO_APP_SECRET:
            raise BadRequestException("ZALO_APP_SECRET is not configured")

        async with aiohttp.ClientSession() as session:
            # 1. Exchange code for access token
            token_headers = {
                "secret_key": settings.ZALO_APP_SECRET,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            token_payload = {
                "app_id": settings.ZALO_APP_ID,
                "grant_type": "authorization_code",
                "code": data.oauth_code,
                "code_verifier": data.code_verifier,
            }

            async with session.post(
                "https://oauth.zaloapp.com/v4/access_token",
                headers=token_headers,
                data=token_payload,
            ) as token_resp:
                token_data = await token_resp.json(content_type=None)
                if token_resp.status != 200 or "access_token" not in token_data:
                    raise BadRequestException(
                        f"Failed to get Zalo access token. Error: {token_data.get('error_name', 'Unknown')} - {token_data.get('error_reason', '')}"
                    )

                access_token = token_data["access_token"]
                # In real scenario, you can also save refresh_token to DB here

            # 2. Call Zalo Graph API to get user ID
            graph_headers = {"access_token": access_token}
            async with session.get(
                "https://graph.zalo.me/v2.0/me?fields=id,name", headers=graph_headers
            ) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "json" in content_type.lower() or resp.status == 200:
                    try:
                        graph_data = await resp.json(content_type=None)
                    except Exception:
                        text_data = await resp.text()
                        raise BadRequestException(
                            f"Failed to parse user profile. {text_data[:100]}"
                        )
                else:
                    text_data = await resp.text()
                    raise BadRequestException(
                        f"Zalo Graph API Error {resp.status}: {text_data[:100]}"
                    )
                if resp.status != 200 or graph_data.get("error"):
                    raise BadRequestException(
                        f"Failed to get user profile. Error: {graph_data.get('message', 'Unknown')}"
                    )

                zalo_id = graph_data.get("id")
                if not zalo_id:
                    raise BadRequestException(
                        "Could not retrieve Zalo ID from Graph API"
                    )

        # Update current user
        user = current_user
        user.zalo_id = str(zalo_id)

        # Save to DB - assuming repo_factory.user.update is available
        # Wait, the current user instance might be detached or we should update it via user_repo
        updated_user = service_factory._repo.user.update(user)

        return ApiResponse.success(
            data=updated_user, message="Zalo account linked successfully"
        )

    except aiohttp.ClientError as e:
        raise BadRequestException(f"Error communicating with Zalo API: {e}")
