"""
Violation Controller — thin FastAPI router.

Only handles HTTP concerns: parse request, call use case, return response.
NO business logic here.
"""

from datetime import date
from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException

from app.core.deps import hasPermission
from app.core.permissions import ViolationPermission
from app.shared.application.response import ApiResponse
from app.user.domain.entity import UserEntity
from app.violation.application import (
    BulkDeleteViolationsUseCase,
    CreateViolationUseCase,
    DeleteViolationUseCase,
    GetViolationsUseCase,
    RestoreViolationUseCase,
    UpdateViolationUseCase,
)
from app.violation.schemas import (
    BulkDeleteViolationsIn,
    ViolationCreate,
    ViolationResponse,
    ViolationUpdate,
)

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("", response_model=ApiResponse[list[ViolationResponse]])
@inject
async def get_violations(
    uc: FromDishka[GetViolationsUseCase],
    _: Annotated[UserEntity, hasPermission(ViolationPermission.READ)],
    user_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
):
    if user_id or month or year or start_date or end_date:
        result = uc.get_by_month(
            user_id=user_id,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )
    else:
        result = uc.get_all(skip=skip, limit=limit, deleted=deleted)
    return ApiResponse.success(data=result)


@router.post("", response_model=ApiResponse[list[ViolationResponse]])
@inject
async def create_violation(
    data: ViolationCreate,
    uc: FromDishka[CreateViolationUseCase],
    _: Annotated[UserEntity, hasPermission(ViolationPermission.CREATE)],
):
    result = await uc.execute(
        user_ids=data.user_ids,
        reason=data.reason,
        date=data.date,
    )
    return ApiResponse.success(data=result)


@router.put("/{item_id}", response_model=ApiResponse[ViolationResponse])
@inject
async def update_violation(
    item_id: int,
    data: ViolationUpdate,
    uc: FromDishka[UpdateViolationUseCase],
    _: Annotated[UserEntity, hasPermission(ViolationPermission.UPDATE)],
):
    result = uc.execute(item_id=item_id, reason=data.reason, date=data.date)
    return ApiResponse.success(data=result)


@router.post("/bulk-delete", response_model=ApiResponse[dict[str, Any]])
@inject
async def bulk_delete_violations(
    data: BulkDeleteViolationsIn,
    uc: FromDishka[BulkDeleteViolationsUseCase],
    _: Annotated[UserEntity, hasPermission(ViolationPermission.DELETE)],
):
    """Xóa hàng loạt các vi phạm theo danh sách IDs."""
    deleted_count = uc.execute(data.ids)
    return ApiResponse.success(data={"deleted_count": deleted_count})


@router.delete("/{item_id}", response_model=ApiResponse[bool])
@inject
async def delete_violation(
    item_id: int,
    uc: FromDishka[DeleteViolationUseCase],
    _: Annotated[UserEntity, hasPermission(ViolationPermission.DELETE)],
):
    result = uc.execute(item_id)
    return ApiResponse.success(data=result)


@router.put("/{item_id}/restore", response_model=ApiResponse[ViolationResponse])
@inject
async def restore_violation(
    item_id: int,
    uc: FromDishka[RestoreViolationUseCase],
    _: Annotated[UserEntity, hasPermission(ViolationPermission.DELETE)],
):
    result = uc.execute(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    return ApiResponse.success(data=result)
