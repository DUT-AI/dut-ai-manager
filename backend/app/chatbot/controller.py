"""Chatbot Controller — FastAPI router handling SSE streaming and Session REST API."""

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.chatbot.application import (
    DeleteChatSessionUseCase,
    GetChatSessionsUseCase,
    GetQuickPromptsUseCase,
    GetSessionMessagesUseCase,
    SendChatMessageUseCase,
)
from app.chatbot.schemas import (
    ChatMessageDto,
    ChatSessionDto,
    QuickPromptItem,
    SendChatRequest,
)
from app.core.deps import CurrentUser
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/chat")
@inject
async def chat_stream(
    request: SendChatRequest,
    current_user: CurrentUser,
    send_uc: FromDishka[SendChatMessageUseCase],
) -> StreamingResponse:
    """Send a message to the chatbot and receive Server-Sent Events (SSE) streaming."""
    generator = send_uc.execute(
        message=request.message,
        session_id=request.session_id,
        user=current_user,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )


@router.get("/sessions", response_model=ApiResponse[list[ChatSessionDto]])
@inject
async def get_sessions(
    current_user: CurrentUser,
    uc: FromDishka[GetChatSessionsUseCase],
) -> ApiResponse[list[ChatSessionDto]]:
    """Get active sessions of current user (max 5)."""
    sessions = uc.execute(current_user.user_id)
    dtos = [
        ChatSessionDto(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]
    return ApiResponse.success(data=dtos)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ApiResponse[list[ChatMessageDto]],
)
@inject
async def get_session_messages(
    session_id: UUID,
    current_user: CurrentUser,
    uc: FromDishka[GetSessionMessagesUseCase],
) -> ApiResponse[list[ChatMessageDto]]:
    """Get all messages of a session owned by current user."""
    messages = uc.execute(session_id, current_user.id)
    dtos = [
        ChatMessageDto(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            metadata_info=m.metadata_info,
            created_at=m.created_at,
        )
        for m in messages
    ]
    return ApiResponse.success(data=dtos)


@router.delete("/sessions/{session_id}", response_model=ApiResponse[bool])
@inject
async def delete_session(
    session_id: UUID,
    current_user: CurrentUser,
    uc: FromDishka[DeleteChatSessionUseCase],
) -> ApiResponse[bool]:
    """Delete a session owned by current user."""
    success = uc.execute(session_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phiên trò chuyện không tồn tại hoặc không thuộc quyền sở hữu",
        )
    return ApiResponse.success(data=True, message="Đã xóa phiên trò chuyện")


@router.get("/quick-prompts", response_model=ApiResponse[list[QuickPromptItem]])
@inject
async def get_quick_prompts(
    current_user: CurrentUser,
    uc: FromDishka[GetQuickPromptsUseCase],
) -> ApiResponse[list[QuickPromptItem]]:
    """Get role-adaptive quick prompts based on user permissions."""
    prompts = uc.execute(current_user)
    return ApiResponse.success(data=prompts)
