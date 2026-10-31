from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import PermissionRequestPermission
from app.permission_request.application import (
    CreatePermissionRequestUseCase,
    DeletePermissionRequestUseCase,
    GetPermissionRequestDetailUseCase,
    GetPermissionRequestsUseCase,
    RestorePermissionRequestUseCase,
    UpdatePermissionRequestUseCase,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.schemas import (
    PermissionRequestCreate,
    PermissionRequestDetailResponse,
    PermissionRequestResponse,
    PermissionRequestUpdate,
)
from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("", response_model=ApiResponse[list[PermissionRequestResponse]])
@inject
async def get_permission_requests(
    uc: FromDishka[GetPermissionRequestsUseCase],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.READ)
    ],
    pagination: Annotated[PaginationParams, Depends()],
    user_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    category: RequestCategory | None = None,
    deleted: bool = False,
):
    """Lấy danh sách các yêu cầu xin phép"""
    items, total = uc.execute(
        user_id=user_id,
        month=month,
        year=year,
        category=category,
        page=pagination.page,
        page_size=pagination.page_size,
        deleted=deleted,
    )
    return ApiResponse.success(
        data=items,
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@router.get(
    "/{request_id}",
    response_model=ApiResponse[PermissionRequestDetailResponse],
)
@inject
async def get_permission_request_detail(
    request_id: int,
    uc: FromDishka[GetPermissionRequestDetailUseCase],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.READ)
    ],
):
    """Lấy chi tiết yêu cầu xin phép (kèm quan hệ đầy đủ)"""
    result = uc.execute(request_id)
    return ApiResponse.success(data=result)


@router.post("", response_model=ApiResponse[PermissionRequestResponse])
@inject
async def create_permission_request(
    data: PermissionRequestCreate,
    uc: FromDishka[CreatePermissionRequestUseCase],
    _current_user: CurrentUser,
):
    """Tạo yêu cầu xin phép mới (bao gồm vắng, trễ, hoãn, đổi ca sinh hoạt)"""
    result = await uc.execute(
        category=data.category,
        note=data.note,
        homework_id=data.homework_id,
        meeting_id=data.meeting_id,
        old_meeting_id=data.old_meeting_id,
        start_time=data.start_time,
        user_id=_current_user.id,
    )
    message = "Tạo yêu cầu xin phép thành công"

    return ApiResponse.success(data=result, message=message)


@router.put("/{request_id}", response_model=ApiResponse[PermissionRequestResponse])
@inject
async def update_permission_request(
    request_id: int,
    data: PermissionRequestUpdate,
    uc: FromDishka[UpdatePermissionRequestUseCase],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.UPDATE)
    ],
):
    """Cập nhật thông tin yêu cầu xin phép"""
    result = await uc.execute(request_id=request_id, data=data)
    return ApiResponse.success(data=result)


@router.delete("/{request_id}", response_model=ApiResponse[bool])
@inject
async def delete_permission_request(
    request_id: int,
    uc: FromDishka[DeletePermissionRequestUseCase],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.DELETE)
    ],
):
    """Xóa yêu cầu (Soft-delete)"""
    result = uc.execute(request_id)
    return ApiResponse.success(data=result)


@router.put(
    "/{request_id}/restore", response_model=ApiResponse[PermissionRequestResponse]
)
@inject
async def restore_permission_request(
    request_id: int,
    uc: FromDishka[RestorePermissionRequestUseCase],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.DELETE)
    ],
):
    """Khôi phục yêu cầu đã xóa"""
    result = uc.execute(request_id)
    if not result:
        raise HTTPException(
            status_code=404, detail="Yêu cầu không tìm thấy hoặc chưa được xóa"
        )
    return ApiResponse.success(data=result)
