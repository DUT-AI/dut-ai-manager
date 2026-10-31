from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import MeetingPermission
from app.meeting.application import (
    CheckInUseCase,
    CheckInWithCardUseCase,
    CheckOutUseCase,
    UpdateParticipantStatusUseCase,
)
from app.meeting.controllers.dependencies import check_meeting_ownership
from app.meeting.schemas import (
    CheckInWithCardRequest,
    CheckOutRequest,
    ParticipantResponse,
    UpdateParticipantStatusRequest,
)
from app.shared.application.response import ApiResponse
from app.utils.text import remove_vietnamese_tones

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post(
    "/check-in-with-card",
    summary="Check-in bằng mã thẻ và trả về audio giọng nói",
    responses={
        200: {
            "content": {"audio/wav": {}},
            "description": "Audio WAV giọng nói thông báo check-in",
        }
    },
)
@inject
async def check_in_with_card(
    body: CheckInWithCardRequest,
    uc: FromDishka[CheckInWithCardUseCase],
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.CHECK_IN)],
):
    """
    Check-in bằng mã thẻ: không yêu cầu JWT (thiết bị quầy).
    Tìm user theo `check_in_card_code`, meeting giao khung ±30 phút quanh hiện tại.
    Trả về dữ liệu âm thanh (WAV) thông báo kết quả điểm danh để thiết bị phát ra loa.
    """
    message, audio_bytes = await uc.execute(card_code=body.card_code)

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'inline; filename="checkin.wav"',
            "X-Message": remove_vietnamese_tones(message),
            "Content-Length": str(len(audio_bytes)),
        },
    )


@router.post("/check-in", response_model=ApiResponse[list[ParticipantResponse]])
@inject
async def check_in(
    uc: FromDishka[CheckInUseCase],
    # _: Annotated[CurrentUser, hasPermission(MeetingPermission.CHECK_IN)],
    user_ids: list[int] = Form(...),
    image: UploadFile = File(...),
    occurred_at: str | None = Form(None),
    check_in_at: str | None = Form(None),
    checkin_at: str | None = Form(None),
    check_in_time: str | None = Form(None),
    checkin_time: str | None = Form(None),
    timestamp: str | None = Form(None),
    client_time: str | None = Form(None),
    client_event_id: str | None = Form(None),
    event_id: str | None = Form(None),
    idempotency_key: str | None = Form(None),
):
    """Thực hiện điểm danh (Check-in)"""
    client_time_val = (
        occurred_at
        or check_in_at
        or checkin_at
        or check_in_time
        or checkin_time
        or timestamp
        or client_time
    )
    idem_key = client_event_id or event_id or idempotency_key

    participants, message = await uc.execute(
        user_ids=user_ids,
        image=image,
        client_time=client_time_val,
        client_event_id=idem_key,
    )
    return ApiResponse.success(
        data=[ParticipantResponse.from_domain(p) for p in participants],
        message=message,
    )


@router.post("/check-out", response_model=ApiResponse[list[ParticipantResponse]])
@inject
async def check_out(
    data: CheckOutRequest,
    uc: FromDishka[CheckOutUseCase],
    # _: Annotated[CurrentUser, hasPermission(MeetingPermission.CHECK_IN)],
):
    """Thực hiện check-out khỏi buổi họp"""
    participants = await uc.execute(
        user_id=data.user_id,
        client_time=data.get_client_time(),
        client_event_id=data.get_idempotency_key(),
    )
    return ApiResponse.success(
        data=[ParticipantResponse.from_domain(p) for p in participants],
        message="Checkout thành công",
    )


@router.put(
    "/{meeting_id}/participants/{user_id}/status",
    response_model=ApiResponse[ParticipantResponse],
)
@inject
async def update_participant_status(
    meeting_id: int,
    user_id: int,
    data: UpdateParticipantStatusRequest,
    uc: FromDishka[UpdateParticipantStatusUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.UPDATE)],
    _: Annotated[None, Depends(check_meeting_ownership)],
):
    """Cập nhật trạng thái thành viên trong buổi họp (Creator/Admin)."""
    participant = uc.execute(
        meeting_id=meeting_id,
        user_id=user_id,
        target_status=data.status,
        check_in_at=data.check_in_at,
        check_out_at=data.check_out_at,
    )
    return ApiResponse.success(
        data=ParticipantResponse.from_domain(participant),
        message="Cập nhật trạng thái thành viên thành công",
    )


__all__ = ["router"]
