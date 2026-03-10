from fastapi import APIRouter, Request
from loguru import logger

from app.core.deps import CurrentUser, ServiceFactoryDI
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/zalo-bot", tags=["zalo-bot"])


@router.get("/generate-bind-code", response_model=ApiResponse[dict])
async def generate_zalo_bot_bind_code(
    service_factory: ServiceFactoryDI,
    current_user: CurrentUser,
):
    """Generate a random 6-character bind code to link Zalo bot."""
    bind_code = service_factory.zalo_bot.generate_bind_code(current_user)
    return ApiResponse.success(
        data={"bind_code": bind_code}, message="Bind code generated successfully"
    )


@router.post("/webhook")
async def zalo_bot_webhook(request: Request, service_factory: ServiceFactoryDI):
    """Handle incoming messages from Zalo Bot Server."""
    body = await request.json()
    result = await service_factory.zalo_bot.handle_webhook(body)
    return result
