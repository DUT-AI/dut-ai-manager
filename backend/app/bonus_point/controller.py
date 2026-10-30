"""
Bonus Point API Controller.

Handles HTTP routes and mapping requests to Use Cases.
"""

from datetime import date
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, HTTPException

from app.bonus_point.application import (
    CreateBonusPointsUseCase,
    DeleteBonusPointUseCase,
    GetBonusPointsUseCase,
    RestoreBonusPointUseCase,
    UpdateBonusPointUseCase,
)
from app.bonus_point.application.dtos import (
    BonusPointCreate,
    BonusPointResponse,
    BonusPointUpdate,
)
from app.bonus_point.domain.value_objects import BonusPointType
from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import BonusPointPermission
from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta

router = APIRouter(prefix="/bonus-points", tags=["bonus-points"])


@router.get(
    "",
    response_model=ApiResponse[list[BonusPointResponse]],
    dependencies=[hasPermission(BonusPointPermission.READ)],
)
@inject
async def get_bonus_points(
    uc: FromDishka[GetBonusPointsUseCase],
    pagination: Annotated[PaginationParams, Depends()],
    user_id: int | None = None,
    type: BonusPointType | None = None,
    month: int | None = None,
    year: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    deleted: bool = False,
):
    """Retrieve bonus points based on filters."""
    items, total = uc.execute(
        user_id=user_id,
        type=type,
        month=month,
        year=year,
        start_date=start_date,
        end_date=end_date,
        page=pagination.page,
        page_size=pagination.page_size,
        deleted=deleted,
    )
    pagination_meta = PaginationMeta.create(
        page=pagination.page, page_size=pagination.page_size, total=total
    )
    return ApiResponse.success(data=items, pagination=pagination_meta)


@router.post(
    "",
    response_model=ApiResponse[list[BonusPointResponse]],
    dependencies=[hasPermission(BonusPointPermission.CREATE)],
)
@inject
async def create_bonus_point(
    data: BonusPointCreate,
    uc: FromDishka[CreateBonusPointsUseCase],
    current_user: CurrentUser,
):
    """Create new bonus point items."""
    result = await uc.execute(data, current_user_name=current_user.name)
    return ApiResponse.success(data=result)


@router.put(
    "/{item_id}",
    response_model=ApiResponse[BonusPointResponse],
    dependencies=[hasPermission(BonusPointPermission.UPDATE)],
)
@inject
async def update_bonus_point(
    item_id: int,
    data: BonusPointUpdate,
    uc: FromDishka[UpdateBonusPointUseCase],
    current_user: CurrentUser,
):
    """Update a bonus point item."""
    result = await uc.execute(item_id, data, current_user_name=current_user.name)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return ApiResponse.success(data=result)


@router.delete(
    "/{item_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(BonusPointPermission.DELETE)],
)
@inject
async def delete_bonus_point(
    item_id: int,
    uc: FromDishka[DeleteBonusPointUseCase],
):
    """Delete a bonus point item."""
    result = await uc.execute(item_id)
    return ApiResponse.success(data=result)


@router.put(
    "/{item_id}/restore",
    response_model=ApiResponse[BonusPointResponse],
    dependencies=[hasPermission(BonusPointPermission.DELETE)],
)
@inject
async def restore_bonus_point(
    item_id: int,
    uc: FromDishka[RestoreBonusPointUseCase],
):
    """Restore a deleted bonus point item."""
    result = uc.execute(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    return ApiResponse.success(data=result)
