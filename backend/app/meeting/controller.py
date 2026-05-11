from datetime import date
from typing import Annotated, List, Optional

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import MeetingPermission
from dishka.integrations.fastapi import FromDishka, inject
from app.meeting.application.use_cases import (
    CheckInUseCase,
    CheckInWithCardUseCase,
    CheckOutUseCase,
    CreateMeetingUseCase,
    DeleteMeetingUseCase,
    GetMeetingsUseCase,
    UpdateMeetingUseCase,
)
from app.meeting.schemas import (
    CheckInWithCardRequest,
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
    ParticipantResponse,
)
from app.shared.application.response import ApiResponse
from app.utils.text import remove_vietnamese_tones
from fastapi import APIRouter, File, Form, UploadFile, status

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


@router.get("", response_model=ApiResponse[List[MeetingResponse]])
@inject
async def get_meetings(
    uc: FromDishka[GetMeetingsUseCase],
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.READ)],
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
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


@router.put("/{meeting_id}", response_model=ApiResponse[MeetingResponse])
@inject
async def update_meeting(
    meeting_id: int,
    data: MeetingUpdate,
    uc: FromDishka[UpdateMeetingUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.UPDATE)],
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
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.DELETE)],
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


@router.post("/check-in", response_model=ApiResponse[List[ParticipantResponse]])
@inject
async def check_in(
    meeting_id: int,
    uc: FromDishka[CheckInUseCase],
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.CHECK_IN)],
    user_ids: List[int] = Form(...),
    image: UploadFile = File(...),
):
    """Thực hiện điểm danh (Check-in)"""
    participants, message = await uc.execute(
        meeting_id=meeting_id, user_ids=user_ids, image=image
    )
    return ApiResponse.success(
        data=[ParticipantResponse.from_domain(p) for p in participants],
        message=message,
    )


@router.post("/{meeting_id}/check-out", response_model=ApiResponse[ParticipantResponse])
@inject
async def check_out(
    meeting_id: int,
    uc: FromDishka[CheckOutUseCase],
    current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.CHECK_IN)],
):
    """Thực hiện check-out khỏi buổi họp"""
    participant = await uc.execute(
        meeting_id=meeting_id,
        user_id=current_user.id,
    )
    return ApiResponse.success(
        data=ParticipantResponse.from_domain(participant),
        message="Checkout thành công",
    )
