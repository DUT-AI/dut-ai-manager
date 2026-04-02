from datetime import date
from typing import Annotated, List, Optional

from app.core.deps import CurrentUser
from app.meeting.application.use_cases import (
    CheckInUseCase,
    CheckInWithCardUseCase,
    CreateMeetingUseCase,
    DeleteMeetingUseCase,
    GetMeetingsUseCase,
    UpdateMeetingUseCase,
)
from app.meeting.deps import (
    get_check_in_uc,
    get_check_in_with_card_uc,
    get_create_meeting_uc,
    get_delete_meeting_uc,
    get_meetings_uc,
    get_update_meeting_uc,
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
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post(
    "", response_model=ApiResponse[MeetingResponse], status_code=status.HTTP_201_CREATED
)
async def create_meeting(
    data: MeetingCreate,
    uc: Annotated[CreateMeetingUseCase, Depends(get_create_meeting_uc)],
    _current_user: CurrentUser,
):
    """Tạo mới buổi họp (Admin/Leader)"""
    meeting = await uc.execute(
        title=data.title,
        content=data.content,
        start_time=data.start_time,
        end_time=data.end_time,
        require_check_in=data.require_check_in,
        user_ids=data.user_ids,
    )
    return ApiResponse.success(
        data=MeetingResponse.from_domain(meeting),
        message="Meeting created successfully",
    )


@router.get("", response_model=ApiResponse[List[MeetingResponse]])
async def get_meetings(
    uc: Annotated[GetMeetingsUseCase, Depends(get_meetings_uc)],
    _current_user: CurrentUser,
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
        deleted=deleted
    )
    return ApiResponse.success(
        data=[MeetingResponse.from_domain(m) for m in meetings],
        message="Meetings retrieved successfully",
    )


@router.get("/{meeting_id}", response_model=ApiResponse[MeetingResponse])
async def get_meeting(
    meeting_id: int,
    uc: Annotated[GetMeetingsUseCase, Depends(get_meetings_uc)],
    _current_user: CurrentUser,
):
    """Lấy thông tin chi tiết buổi họp"""
    meeting = uc.get_by_id(meeting_id)
    return ApiResponse.success(
        data=MeetingResponse.from_domain(meeting),
        message="Meeting retrieved successfully",
    )


@router.put("/{meeting_id}", response_model=ApiResponse[MeetingResponse])
async def update_meeting(
    meeting_id: int,
    data: MeetingUpdate,
    uc: Annotated[UpdateMeetingUseCase, Depends(get_update_meeting_uc)],
    _current_user: CurrentUser,
):
    """Cập nhật thông tin buổi họp"""
    meeting = await uc.execute(meeting_id=meeting_id, data=data)
    return ApiResponse.success(
        data=MeetingResponse.from_domain(meeting),
        message="Meeting updated successfully",
    )


@router.delete("/{meeting_id}", response_model=ApiResponse[bool])
async def delete_meeting(
    meeting_id: int,
    uc: Annotated[DeleteMeetingUseCase, Depends(get_delete_meeting_uc)],
    _current_user: CurrentUser,
):
    """Xóa buổi họp"""
    result = uc.execute(meeting_id=meeting_id)
    return ApiResponse.success(data=result, message="Meeting deleted successfully")


@router.post(
    "/check-in-with-card",
    response_model=ApiResponse[None],
)
async def check_in_with_card(
    body: CheckInWithCardRequest,
    uc: Annotated[CheckInWithCardUseCase, Depends(get_check_in_with_card_uc)],
):
    """
    Check-in bằng mã thẻ: không yêu cầu JWT (thiết bị quầy).
    Tìm user theo `check_in_card_code`, meeting giao khung ±30 phút quanh hiện tại.
    """
    message = await uc.execute(card_code=body.card_code)
    return ApiResponse.success(
        data=None, message=remove_vietnamese_tones(message)
    )


@router.post("/check-in", response_model=ApiResponse[List[ParticipantResponse]])
async def check_in(
    meeting_id: int,
    uc: Annotated[CheckInUseCase, Depends(get_check_in_uc)],
    _current_user: CurrentUser,
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
