from app.core.deps import CurrentUser, ServiceFactoryDI, hasPermission
from app.core.permissions import PermissionRequestPermission
from app.models.user import User
from typing import Annotated
from app.schemas.permission_request import (
    PermissionRequestCreate,
    PermissionRequestResponse,
    PermissionRequestUpdate,
)
from app.schemas.response import ApiResponse
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/permissions", tags=["permissions"])


# --- Permission Requests CRUD ---
@router.get("", response_model=ApiResponse[list[PermissionRequestResponse]])
async def get_permission_requests(
    _: Annotated[User, hasPermission(PermissionRequestPermission.READ)],
    service_factory: ServiceFactoryDI,
    user_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    if user_id:
        result = service_factory.permission_request.get_by_user(
            user_id=user_id, month=month, year=year
        )
    else:
        result = service_factory.permission_request.get_all(skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[PermissionRequestResponse],
    dependencies=[hasPermission(PermissionRequestPermission.CREATE)],
)
async def create_permission_request(
    data: PermissionRequestCreate,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.permission_request.create(data)
    return ApiResponse.success(data=result)


@router.put(
    "/{request_id}",
    response_model=ApiResponse[PermissionRequestResponse],
    dependencies=[
        hasPermission(PermissionRequestPermission.UPDATE),
    ],
)
async def update_permission_request(
    request_id: int,
    data: PermissionRequestUpdate,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.permission_request.update(request_id, data)
    return ApiResponse.success(data=result)


@router.delete(
    "/{request_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(PermissionRequestPermission.DELETE)],
)
async def delete_permission_request(
    request_id: int,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.permission_request.delete(request_id)
    return ApiResponse.success(data=result)
