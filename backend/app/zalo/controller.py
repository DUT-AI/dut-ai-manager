from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from app.core.deps import CurrentUser
from app.shared.application.response import ApiResponse
from app.zalo.application.use_cases import (
    BindZaloAccountUseCase,
    GenerateBotBindCodeUseCase,
    GetZaloLoginUrlUseCase,
    HandleBotWebhookUseCase,
    HandleMiniAppWebhookUseCase,
)
from app.zalo.deps import (
    get_bind_account_uc,
    get_generate_bot_code_uc,
    get_handle_bot_webhook_uc,
    get_handle_miniapp_webhook_uc,
    get_login_url_uc,
)
from app.zalo.schemas import ZaloBindCodeResponse, ZaloBindRequest, ZaloLoginUrlResponse

router = APIRouter(prefix="/zalo", tags=["Zalo"])


@router.get("/login-url", response_model=ApiResponse[ZaloLoginUrlResponse])
async def get_zalo_login_url(
    uc: Annotated[GetZaloLoginUrlUseCase, Depends(get_login_url_uc)],
    _current_user: Annotated[CurrentUser, Depends()],
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
async def bind_zalo(
    data: ZaloBindRequest,
    uc: Annotated[BindZaloAccountUseCase, Depends(get_bind_account_uc)],
    current_user: Annotated[CurrentUser, Depends()],
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
async def generate_zalo_bot_bind_code(
    uc: Annotated[GenerateBotBindCodeUseCase, Depends(get_generate_bot_code_uc)],
    current_user: Annotated[CurrentUser, Depends()],
):
    """Tạo mã 6 ký tự để người dùng chat với bot để liên kết."""
    bind_code = uc.execute(current_user.id or 0)
    return ApiResponse.success(data=ZaloBindCodeResponse(bind_code=bind_code))


@router.post("/bot/webhook")
async def zalo_bot_webhook(
    request: Request,
    uc: Annotated[HandleBotWebhookUseCase, Depends(get_handle_bot_webhook_uc)],
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
async def zalo_miniapp_webhook(
    request: Request,
    uc: Annotated[HandleMiniAppWebhookUseCase, Depends(get_handle_miniapp_webhook_uc)],
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
