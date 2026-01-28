from typing import Annotated

from app.core.deps import ServiceFactoryDI
from app.core.deps import hasPermission
from app.core.permissions import ViolationPermission
from app.models.user import User
from app.schemas.activity import (
    ViolationCreate,
    ViolationResponse,
    ViolationUpdate,
)
from app.schemas.response import ApiResponse
from fastapi import APIRouter

router = APIRouter(prefix="/violations", tags=["violations"])


# --- Violations CRUD ---
@router.get("", response_model=ApiResponse[list[ViolationResponse]])
async def get_violations(
    _: Annotated[User, hasPermission(ViolationPermission.READ)],
    service_factory: ServiceFactoryDI,
    user_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    if user_id:
        result = service_factory.violation.get(user_id=user_id, month=month, year=year)
    else:
        result = service_factory.violation.get_all(skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.post("", response_model=ApiResponse[list[ViolationResponse]])
async def create_violation(
    data: ViolationCreate,
    _: Annotated[User, hasPermission(ViolationPermission.CREATE)],
    service_factory: ServiceFactoryDI,
):
    result = await service_factory.violation.create(data)
    return ApiResponse.success(data=result)


@router.put("/{item_id}", response_model=ApiResponse[ViolationResponse])
async def update_violation(
    item_id: int,
    data: ViolationUpdate,
    _: Annotated[User, hasPermission(ViolationPermission.UPDATE)],
    service_factory: ServiceFactoryDI,
):
    result = service_factory.violation.update(item_id, data)
    return ApiResponse.success(data=result)


@router.delete("/{item_id}", response_model=ApiResponse[bool])
async def delete_violation(
    item_id: int,
    _: Annotated[User, hasPermission(ViolationPermission.DELETE)],
    service_factory: ServiceFactoryDI,
):
    result = service_factory.violation.delete(item_id)
    return ApiResponse.success(data=result)
