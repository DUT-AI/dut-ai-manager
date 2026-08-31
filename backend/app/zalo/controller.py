from typing import Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Request

from app.core.deps import CurrentUser
from app.shared.application.response import ApiResponse
from app.zalo.application.use_cases import (
    BindZaloAccountUseCase,
    GenerateBotBindCodeUseCase,
    GetZaloLoginUrlUseCase,
    HandleBotWebhookUseCase,
    HandleMiniAppWebhookUseCase,
)
from app.zalo.schemas import ZaloBindCodeResponse, ZaloBindRequest, ZaloLoginUrlResponse

router = APIRouter(prefix="/zalo", tags=["Zalo"])


@router.get("/login-url", response_model=ApiResponse[ZaloLoginUrlResponse])
@inject
async def get_zalo_login_url(
    uc: FromDishka[GetZaloLoginUrlUseCase],
    _current_user: CurrentUser,
):
    """
    Tạo Zalo Login URL sử dụng PKCE.
    Trả về URL và code_verifier để frontend lưu trữ.
    """
    state = uc.execute()
    return ApiResponse.success(
        data=ZaloLoginUrlResponse(
            login_url=state.login_url, code_verifier=state.code_verifier
        )
    )


@router.post("/bind", response_model=ApiResponse[dict[str, Any]])
@inject
async def bind_zalo(
    data: ZaloBindRequest,
    uc: FromDishka[BindZaloAccountUseCase],
    current_user: CurrentUser,
):
    """
    Liên kết tài khoản Zalo bằng oauth_code.
    """
    profile = await uc.execute(
        user_id=current_user.id or 0,
        oauth_code=data.oauth_code,
        code_verifier=data.code_verifier,
    )
    return ApiResponse.success(
        data=profile.model_dump(), message="Liên kết tài khoản Zalo thành công"
    )


@router.get("/bot/generate-bind-code", response_model=ApiResponse[ZaloBindCodeResponse])
@inject
async def generate_zalo_bot_bind_code(
    uc: FromDishka[GenerateBotBindCodeUseCase],
    current_user: CurrentUser,
):
    """Tạo mã 6 ký tự để người dùng chat với bot để liên kết."""
    bind_code = uc.execute(current_user.id or 0)
    return ApiResponse.success(data=ZaloBindCodeResponse(bind_code=bind_code))


@router.post("/bot/webhook")
@inject
async def zalo_bot_webhook(
    request: Request,
    uc: FromDishka[HandleBotWebhookUseCase],
):
    """Xử lý webhook từ Zalo Bot Platform."""
    body = await request.json()
    result = await uc.execute(body)
    return result


@router.get("/webhook")
@router.get("/miniapp/webhook")
async def zalo_miniapp_webhook_health():
    """Endpoint xác thực webhook URL từ Zalo Platform (GET check)."""
    return {"error": 0, "message": "Zalo Mini App Webhook is active"}


@router.post("/webhook")
@router.post("/miniapp/webhook")
@inject
async def zalo_miniapp_webhook(
    request: Request,
    uc: FromDishka[HandleMiniAppWebhookUseCase],
):
    """
    Xử lý Webhook từ Zalo Mini App Open APIs Platform.
    Tự động xác thực chữ ký X-ZEvent-Signature và xử lý các sự kiện:
    - versions.review.done: Xét duyệt phiên bản hoàn tất
    - user_follow_oa, user_unfollow_oa, user_submit_info, v.v.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    headers = dict(request.headers)
    result = await uc.execute(headers=headers, body=body)
    return result
