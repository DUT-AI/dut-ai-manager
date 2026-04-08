from typing import Annotated, List, Optional

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import PermissionRequestPermission
from app.permission_request.application.use_cases import (
    CreatePermissionRequestUseCase,
    DeletePermissionRequestUseCase,
    GetPermissionRequestsUseCase,
    RestorePermissionRequestUseCase,
    UpdatePermissionRequestUseCase,
)
from app.permission_request.deps import (
    get_create_request_uc,
    get_delete_request_uc,
    get_requests_uc,
    get_restore_request_uc,
    get_update_request_uc,
)
from app.permission_request.schemas import (
    PermissionRequestCreate,
    PermissionRequestResponse,
    PermissionRequestUpdate,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.application.response import ApiResponse
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("", response_model=ApiResponse[List[PermissionRequestResponse]])
async def get_permission_requests(
    uc: Annotated[GetPermissionRequestsUseCase, Depends(get_requests_uc)],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.READ)
    ],
    user_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    category: Optional[RequestCategory] = None,
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
):
    """Lấy danh sách các yêu cầu xin phép"""
    results = uc.execute(
        user_id=user_id,
        month=month,
        year=year,
        category=category,
        skip=skip,
        limit=limit,
        deleted=deleted
    )
    return ApiResponse.success(data=results)


@router.post("", response_model=ApiResponse[PermissionRequestResponse])
async def create_permission_request(
    data: PermissionRequestCreate,
    uc: Annotated[CreatePermissionRequestUseCase, Depends(get_create_request_uc)],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.CREATE)
    ],
):
    """Tạo yêu cầu xin phép mới"""
    result = await uc.execute(
        category=data.category,
        note=data.note,
        homework_id=data.homework_id,
        meeting_id=data.meeting_id,
        start_time=data.start_time
    )
    return ApiResponse.success(data=result)


@router.put("/{request_id}", response_model=ApiResponse[PermissionRequestResponse])
async def update_permission_request(
    request_id: int,
    data: PermissionRequestUpdate,
    uc: Annotated[UpdatePermissionRequestUseCase, Depends(get_update_request_uc)],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.UPDATE)
    ],
):
    """Cập nhật thông tin yêu cầu xin phép"""
    result = await uc.execute(request_id=request_id, data=data)
    return ApiResponse.success(data=result)


@router.delete("/{request_id}", response_model=ApiResponse[bool])
async def delete_permission_request(
    request_id: int,
    uc: Annotated[DeletePermissionRequestUseCase, Depends(get_delete_request_uc)],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.DELETE)
    ],
):
    """Xóa yêu cầu (Soft-delete)"""
    result = uc.execute(request_id)
    return ApiResponse.success(data=result)


@router.put("/{request_id}/restore", response_model=ApiResponse[bool])
async def restore_permission_request(
    request_id: int,
    uc: Annotated[RestorePermissionRequestUseCase, Depends(get_restore_request_uc)],
    _current_user: Annotated[
        CurrentUser, hasPermission(PermissionRequestPermission.DELETE)
    ],
):
    """Khôi phục yêu cầu đã xóa"""
    result = uc.execute(request_id)
    return ApiResponse.success(data=result)
