"""
Duty Controller — REST API Endpoints.
"""

import json
from datetime import date
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import DutyPermission
from app.duty.application.dtos import (
    BatchCreateDutyRequest,
    DutyResponse,
    RejectDutyRequest,
    ToggleDutyScheduleRequest,
    UpdateDutyRequest,
    WeeklyDutyClassDto,
)
from app.duty.application.get_duties_use_case import GetDutiesUseCase
from app.duty.application.manage_duty_use_case import (
    DeleteDutyUseCase,
    RestoreDutyUseCase,
    UpdateDutyUseCase,
)
from app.duty.application.review_duty_use_case import (
    ApproveDutyUseCase,
    RejectDutyUseCase,
)
from app.duty.application.submit_duty_evidence_use_case import (
    SubmitDutyEvidenceUseCase,
)
from app.duty.application.toggle_duty_schedule_use_case import (
    BatchCreateDutyUseCase,
    ToggleDutyScheduleUseCase,
)
from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta

router = APIRouter(prefix="/duties", tags=["Duties"])


@router.get(
    "/weekly",
    response_model=ApiResponse[list[WeeklyDutyClassDto]],
)
@inject
async def get_weekly_schedule(
    uc: FromDishka[GetDutiesUseCase],
    _current_user: CurrentUser,
    target_date: date | None = None,
):
    """
    Lấy lịch trực nhật 4 ngày trong tuần của 4 lớp Gen 2 (Thứ 3, 4, 5, 7).
    Tất cả thành viên đều có quyền xem.
    """
    schedule = uc.get_weekly_schedule(target_date)
    return ApiResponse.success(
        data=schedule,
        message="Lấy lịch trực nhật tuần thành công",
    )


@router.get(
    "",
    response_model=ApiResponse[list[DutyResponse]],
)
@inject
async def get_duties(
    uc: FromDishka[GetDutiesUseCase],
    pagination: Annotated[PaginationParams, Depends()],
    _current_user: CurrentUser,
    start_date: date | None = None,
    end_date: date | None = None,
    team_id: int | None = None,
    status: str | None = None,
):
    """
    Lấy danh sách các ca trực nhật có hỗ trợ lọc và phân trang.
    Tất cả thành viên đều có quyền xem.
    """
    duties, total = uc.execute(
        start_date=start_date,
        end_date=end_date,
        team_id=team_id,
        status=status,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    meta = PaginationMeta.create(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
    return ApiResponse.success(
        data=duties,
        pagination=meta,
        message="Lấy danh sách trực nhật thành công",
    )


@router.get(
    "/{duty_id}",
    response_model=ApiResponse[DutyResponse],
)
@inject
async def get_duty_by_id(
    duty_id: int,
    uc: FromDishka[GetDutiesUseCase],
    _current_user: CurrentUser,
):
    """Lấy chi tiết một ca trực nhật."""
    duty = uc.get_by_id(duty_id)
    if not duty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ca trực nhật không tồn tại",
        )
    return ApiResponse.success(data=duty, message="Lấy ca trực nhật thành công")


@router.post(
    "/toggle-schedule",
    response_model=ApiResponse[DutyResponse | None],
)
@inject
async def toggle_duty_schedule(
    body: ToggleDutyScheduleRequest,
    uc: FromDishka[ToggleDutyScheduleUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(DutyPermission.CREATE)],
):
    """
    Bật hoặc tắt lịch trực nhật cho một ngày và nhóm Gen 2 cụ thể.
    Dành cho người có quyền duty:create (Admin / HR).
    """
    result = await uc.execute(
        duty_date=body.duty_date,
        team_id=body.team_id,
        enabled=body.enabled,
        start_time=body.start_time,
        end_time=body.end_time,
        meeting_id=body.meeting_id,
        checklist=body.checklist,
        note=body.note,
    )
    action_text = "bật" if body.enabled else "hủy"
    return ApiResponse.success(
        data=result,
        message=f"Đã {action_text} lịch trực nhật thành công",
    )


@router.post(
    "/batch-schedule",
    response_model=ApiResponse[list[DutyResponse]],
)
@inject
async def batch_create_duties(
    body: BatchCreateDutyRequest,
    uc: FromDishka[BatchCreateDutyUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(DutyPermission.CREATE)],
):
    """
    Tạo lịch trực nhật tự do cho một hoặc nhiều nhóm phụ trách cùng lúc.
    Dành cho người có quyền duty:create (Admin / HR).
    """
    result = await uc.execute(
        team_ids=body.team_ids,
        duty_date=body.duty_date,
        start_time=body.start_time,
        end_time=body.end_time,
        checklist=body.checklist,
        note=body.note,
    )
    return ApiResponse.success(
        data=result,
        message=f"Đã tạo thành công {len(result)} ca trực nhật cho các nhóm được chọn",
    )


@router.put(
    "/{duty_id}",
    response_model=ApiResponse[DutyResponse],
)
@inject
async def update_duty(
    duty_id: int,
    body: UpdateDutyRequest,
    uc: FromDishka[UpdateDutyUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(DutyPermission.UPDATE)],
):
    """
    Cập nhật checklist nội dung hoặc ghi chú phân công ca trực nhật.
    Dành cho người có quyền duty:update (Admin / HR).
    """
    result = await uc.execute(duty_id=duty_id, req=body)
    return ApiResponse.success(
        data=result,
        message="Cập nhật thông tin ca trực nhật thành công",
    )


@router.delete(
    "/{duty_id}",
    response_model=ApiResponse[None],
)
@inject
async def delete_duty(
    duty_id: int,
    uc: FromDishka[DeleteDutyUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(DutyPermission.DELETE)],
):
    """
    Xóa ca trực nhật (soft delete).
    Dành cho người có quyền duty:delete (Admin / HR).
    """
    await uc.execute(duty_id=duty_id)
    return ApiResponse.success(
        data=None,
        message="Đã xóa ca trực nhật thành công",
    )


@router.post(
    "/{duty_id}/submit",
    response_model=ApiResponse[DutyResponse],
)
@inject
async def submit_duty_evidence(
    duty_id: int,
    uc: FromDishka[SubmitDutyEvidenceUseCase],
    current_user: CurrentUser,
    files: list[UploadFile] = File(...),
    checklist: str | None = Form(None),
    custom_checklist: str | None = Form(None),
    note: str | None = Form(None),
):
    """
    Nộp ảnh thành phẩm thực tế, checklist và ghi chú trực nhật.
    Chỉ cần 1 người đại diện trong nhóm nộp và tối thiểu 1 ảnh trước 22:00.
    """

    roles_lower = [r.lower() for r in current_user.role_names]
    is_admin = (
        current_user.has_permission(DutyPermission.UPDATE.value)
        or current_user.has_permission(DutyPermission.CREATE.value)
        or any(r in ["admin", "hr"] for r in roles_lower)
    )

    raw_checklist = checklist or custom_checklist
    parsed_checklist = None
    if raw_checklist:
        try:
            parsed_checklist = json.loads(raw_checklist)
        except Exception:
            pass

    result = await uc.execute(
        duty_id=duty_id,
        user_id=current_user.id or 0,
        files=files,
        checklist=parsed_checklist,
        note=note,
        is_admin=is_admin,
    )
    return ApiResponse.success(
        data=result,
        message="Nộp minh chứng trực nhật thành công, đang chờ Admin/HR duyệt",
    )


@router.post(
    "/{duty_id}/approve",
    response_model=ApiResponse[DutyResponse],
)
@inject
async def approve_duty(
    duty_id: int,
    uc: FromDishka[ApproveDutyUseCase],
    current_user: Annotated[CurrentUser, hasPermission(DutyPermission.UPDATE)],
):
    """
    Duyệt minh chứng trực nhật -> chuyển thành COMPLETED.
    Chỉ người có quyền duty:update (Admin / HR) mới được duyệt. Teammate KHÔNG có quyền này.
    """
    result = await uc.execute(duty_id=duty_id, admin_id=current_user.id or 0)
    return ApiResponse.success(
        data=result,
        message="Đã duyệt ca trực nhật thành công",
    )


@router.post(
    "/{duty_id}/reject",
    response_model=ApiResponse[DutyResponse],
)
@inject
async def reject_duty(
    duty_id: int,
    body: RejectDutyRequest,
    uc: FromDishka[RejectDutyUseCase],
    current_user: Annotated[CurrentUser, hasPermission(DutyPermission.UPDATE)],
):
    """
    Từ chối minh chứng trực nhật kèm lý do để học viên làm lại.
    Chỉ người có quyền duty:update (Admin / HR) mới được từ chối. Teammate KHÔNG có quyền này.
    """
    result = await uc.execute(
        duty_id=duty_id,
        admin_id=current_user.id or 0,
        reason=body.reason,
    )
    return ApiResponse.success(
        data=result,
        message="Đã từ chối minh chứng ca trực nhật",
    )


@router.post(
    "/{duty_id}/restore",
    response_model=ApiResponse[DutyResponse],
)
@inject
async def restore_duty(
    duty_id: int,
    uc: FromDishka[RestoreDutyUseCase],
    _current_user: Annotated[CurrentUser, hasPermission(DutyPermission.UPDATE)],
):
    """
    Hồi phục ca trực nhật đã bị hủy (CANCELLED) về lại trạng thái PENDING.
    Dành cho người có quyền duty:update (Admin / HR).
    """
    result = await uc.execute(duty_id=duty_id)
    return ApiResponse.success(
        data=result,
        message="Hồi phục ca trực nhật thành công",
    )


