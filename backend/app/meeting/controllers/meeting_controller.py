from datetime import date, datetime
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import MeetingPermission
from app.meeting.application import (
    CalculateCurrentCapacityUseCase,
    CreateMeetingUseCase,
    DeleteMeetingUseCase,
    GetMeetingsUseCase,
    GetUpcomingMeetingsWithSeatsUseCase,
    UpdateMeetingUseCase,
)
from app.meeting.controllers.dependencies import check_meeting_ownership
from app.meeting.domain.value_objects import CapacityMonitor
from app.meeting.schemas import (
    MeetingCreate,
    MeetingDetailResponse,
    MeetingResponse,
    MeetingSeatAvailabilityDto,
    MeetingUpdate,
)
from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta
from app.shared.infrastructure.sse import sse_broadcaster

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.get(
    "/available-seats", response_model=ApiResponse[list[MeetingSeatAvailabilityDto]]
)
@inject
async def get_upcoming_meetings_with_seats(
    uc: FromDishka[GetUpcomingMeetingsWithSeatsUseCase],
    _current_user: CurrentUser,
    from_date: datetime | None = None,
):
    """Lấy danh sách các buổi họp sắp tới kèm số lượng ghế khả dụng"""
    results = uc.execute(from_date=from_date)
    return ApiResponse.success(data=results)


@router.post(
    "", response_model=ApiResponse[MeetingResponse], status_code=status.HTTP_201_CREATED
)
@inject
async def create_meeting(
    data: MeetingCreate,
    uc: FromDishka[CreateMeetingUseCase],
    current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.CREATE)],
):
    """Tạo mới buổi họp (Admin/Leader)"""
    meeting = await uc.execute(
        title=data.title,
        content=data.content,
        start_time=data.start_time,
        end_time=data.end_time,
        require_check_in=data.require_check_in,
        enable_evaluation=data.enable_evaluation,
        user_ids=data.user_ids,
        creator_id=current_user.id,
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
    pagination: Annotated[PaginationParams, Depends()],
    start_date: date | None = None,
    end_date: date | None = None,
    deleted: bool = False,
):
    """Lấy danh sách các buổi họp (metadata rút gọn, hỗ trợ phân trang)"""
    is_calendar_view = start_date is not None and end_date is not None
    meetings, total = uc.execute(
        page=pagination.page,
        page_size=pagination.page_size,
        start_date=start_date,
        end_date=end_date,
        deleted=deleted,
        all_records=is_calendar_view,
    )
    meta = (
        None
        if is_calendar_view
        else PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )
    )
    return ApiResponse.success(
        data=[MeetingResponse.from_domain(m) for m in meetings],
        message="Meetings retrieved successfully",
        pagination=meta,
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


@router.get("/{meeting_id}", response_model=ApiResponse[MeetingDetailResponse])
@inject
async def get_meeting(
    meeting_id: int,
    uc: FromDishka[GetMeetingsUseCase],
    _: Annotated[CurrentUser, hasPermission(MeetingPermission.READ)],
):
    """Lấy thông tin chi tiết buổi họp kèm danh sách người tham gia"""
    meeting = uc.get_by_id(meeting_id)
    return ApiResponse.success(
        data=MeetingDetailResponse.from_domain(meeting),
        message="Meeting retrieved successfully",
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


__all__ = ["router"]
