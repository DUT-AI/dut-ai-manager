from datetime import date
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import MeetingPermission
from app.meeting.application.capacity_use_cases import CalculateCurrentCapacityUseCase
from app.meeting.application.use_cases import (
    CheckInUseCase,
    CheckInWithCardUseCase,
    CheckOutUseCase,
    CreateMeetingUseCase,
    DeleteMeetingUseCase,
    GetMeetingsUseCase,
    UpdateMeetingUseCase,
)
from app.meeting.domain.value_objects import CapacityMonitor
from app.meeting.schemas import (
    CheckInWithCardRequest,
    CheckOutRequest,
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
    ParticipantResponse,
)
from app.shared.application.response import ApiResponse, BadRequestException
from app.shared.infrastructure.sse import sse_broadcaster
from app.utils.text import remove_vietnamese_tones

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post(
    "", response_model=ApiResponse[MeetingResponse], status_code=status.HTTP_201_CREATED
)
@inject
async def create_meeting(
    data: MeetingCreate,
    uc: FromDishka[CreateMeetingUseCase],
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.CREATE)],
):
    """Tạo mới buổi họp (Admin/Leader)"""
    meeting = await uc.execute(
        title=data.title,
        content=data.content,
        start_time=data.start_time,
        end_time=data.end_time,
        require_check_in=data.require_check_in,
        user_ids=data.user_ids,
        team_ids=data.team_ids,
    )
    return ApiResponse.success(
        data=MeetingResponse.from_domain(meeting),
        message="Meeting created successfully",
    )


@router.get("", response_model=ApiResponse[list[MeetingResponse]])
@inject
async def get_meetings(
    uc: FromDishka[GetMeetingsUseCase],
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.READ)],
    skip: int = 0,
    limit: int = 100,
    start_date: date | None = None,
    end_date: date | None = None,
    deleted: bool = False,
):
    """Lấy danh sách các buổi họp"""
    meetings = uc.execute(
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        deleted=deleted,
    )
    return ApiResponse.success(
        data=[MeetingResponse.from_domain(m) for m in meetings],
        message="Meetings retrieved successfully",
    )


@router.get("/{meeting_id}", response_model=ApiResponse[MeetingResponse])
@inject
async def get_meeting(
    meeting_id: int,
    uc: FromDishka[GetMeetingsUseCase],
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.READ)],
):
    """Lấy thông tin chi tiết buổi họp"""
    meeting = uc.get_by_id(meeting_id)
    return ApiResponse.success(
        data=MeetingResponse.from_domain(meeting),
        message="Meeting retrieved successfully",
    )


@inject
async def check_meeting_ownership(
    meeting_id: int,
    current_user: CurrentUser,
    uc: FromDishka[GetMeetingsUseCase],
):
    """Kiểm tra xem người dùng hiện tại có quyền sở hữu cuộc họp (hoặc là Admin) không"""
    meeting = uc.get_by_id(meeting_id)
    if current_user.role_name != "admin" and meeting.created_by != current_user.id:
        raise BadRequestException(
            message="Bạn không có quyền chỉnh sửa hoặc xóa buổi họp này",
            status_code=status.HTTP_403_FORBIDDEN,
        )


@router.put("/{meeting_id}", response_model=ApiResponse[MeetingResponse])
@inject
async def update_meeting(
    meeting_id: int,
    data: MeetingUpdate,
    uc: FromDishka[UpdateMeetingUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.UPDATE)],
    _: Annotated[None, Depends(check_meeting_ownership)],
):
    """Cập nhật thông tin buổi họp"""
    meeting = await uc.execute(meeting_id=meeting_id, data=data)
    return ApiResponse.success(
        data=MeetingResponse.from_domain(meeting),
        message="Meeting updated successfully",
    )


@router.delete("/{meeting_id}", response_model=ApiResponse[bool])
@inject
async def delete_meeting(
    meeting_id: int,
    uc: FromDishka[DeleteMeetingUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.DELETE)],
    _: Annotated[None, Depends(check_meeting_ownership)],
):
    """Xóa buổi họp"""
    result = uc.execute(meeting_id=meeting_id)
    return ApiResponse.success(data=result, message="Meeting deleted successfully")


@router.post(
    "/check-in-with-card",
    response_model=ApiResponse[None],
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
    """
    message = await uc.execute(card_code=body.card_code)
    return ApiResponse.success(data=None, message=remove_vietnamese_tones(message))


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
        occurred_at or check_in_at or checkin_at or check_in_time or
        checkin_time or timestamp or client_time
    )
    idem_key = client_event_id or event_id or idempotency_key

    participants, message = await uc.execute(
        user_ids=user_ids, 
        image=image, 
        client_time=client_time_val, 
        client_event_id=idem_key
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
        client_event_id=data.get_idempotency_key()
    )
    return ApiResponse.success(
        data=[ParticipantResponse.from_domain(p) for p in participants],
        message="Checkout thành công",
    )


@router.get("/events/stream")
async def stream_meeting_events():
    """Stream các sự kiện check-in/out theo thời gian thực (SSE)"""
    return StreamingResponse(
        sse_broadcaster.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering on Nginx
            "X-Content-Type-Options": "nosniff",  # Prevent MIME sniffing
        },
    )


@router.get("/capacity/status", response_model=ApiResponse[CapacityMonitor])
@inject
async def get_capacity_status(
    use_case: FromDishka[CalculateCurrentCapacityUseCase],
):
    """Lấy trạng thái capacity hiện tại"""
    monitor = use_case.execute()
    return ApiResponse.success(data=monitor)


@router.get("/capacity/forecast", response_model=ApiResponse[CapacityMonitor])
@inject
async def get_capacity_forecast(
    use_case: FromDishka[CalculateCurrentCapacityUseCase],
):
    """Lấy dự báo 30 phút tới"""
    monitor = use_case.execute()
    return ApiResponse.success(data=monitor)
