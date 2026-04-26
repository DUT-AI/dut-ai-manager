"""
Violation Controller — thin FastAPI router.

Only handles HTTP concerns: parse request, call use case, return response.
NO business logic here.
"""

from typing import Annotated

from app.core.deps import hasPermission
from app.core.permissions import ViolationPermission
from app.shared.application.response import ApiResponse
from app.user.domain.entity import UserEntity
from app.violation.application.use_cases import (
    CreateViolationUseCase,
    DeleteViolationUseCase,
    GetViolationsUseCase,
    RestoreViolationUseCase,
    UpdateViolationUseCase,
)
from app.violation.deps import (
    get_create_violation_uc,
    get_delete_violation_uc,
    get_restore_violation_uc,
    get_update_violation_uc,
    get_violations_uc,
)
from app.violation.schemas import ViolationCreate, ViolationResponse, ViolationUpdate
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("", response_model=ApiResponse[list[ViolationResponse]])
async def get_violations(
    _: Annotated[UserEntity, hasPermission(ViolationPermission.READ)],
    uc: Annotated[GetViolationsUseCase, Depends(get_violations_uc)],
    user_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
):
    if user_id or month or year:
        result = uc.get_by_month(user_id=user_id, month=month, year=year)
    else:
        result = uc.get_all(skip=skip, limit=limit, deleted=deleted)
    return ApiResponse.success(data=result)


@router.post("", response_model=ApiResponse[list[ViolationResponse]])
async def create_violation(
    data: ViolationCreate,
    _: Annotated[UserEntity, hasPermission(ViolationPermission.CREATE)],
    uc: Annotated[CreateViolationUseCase, Depends(get_create_violation_uc)],
):
    result = await uc.execute(
        user_ids=data.user_ids,
        reason=data.reason,
        date=data.date,
    )
    return ApiResponse.success(data=result)


@router.put("/{item_id}", response_model=ApiResponse[ViolationResponse])
async def update_violation(
    item_id: int,
    data: ViolationUpdate,
    _: Annotated[UserEntity, hasPermission(ViolationPermission.UPDATE)],
    uc: Annotated[UpdateViolationUseCase, Depends(get_update_violation_uc)],
):
    result = uc.execute(item_id=item_id, reason=data.reason, date=data.date)
    return ApiResponse.success(data=result)


@router.delete("/{item_id}", response_model=ApiResponse[bool])
async def delete_violation(
    item_id: int,
    _: Annotated[UserEntity, hasPermission(ViolationPermission.DELETE)],
    uc: Annotated[DeleteViolationUseCase, Depends(get_delete_violation_uc)],
):
    result = uc.execute(item_id)
    return ApiResponse.success(data=result)


@router.put("/{item_id}/restore", response_model=ApiResponse[ViolationResponse])
async def restore_violation(
    item_id: int,
    _: Annotated[UserEntity, hasPermission(ViolationPermission.DELETE)],
    uc: Annotated[RestoreViolationUseCase, Depends(get_restore_violation_uc)],
):
    result = uc.execute(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    return ApiResponse.success(data=result)
