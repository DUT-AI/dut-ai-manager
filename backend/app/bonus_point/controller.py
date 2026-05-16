"""
Bonus Point API Controller.

Handles HTTP routes and mapping requests to Use Cases.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.bonus_point.application.dtos import (
    BonusPointCreate,
    BonusPointResponse,
    BonusPointUpdate,
)
from app.bonus_point.application.use_cases import (
    CreateBonusPointsUseCase,
    DeleteBonusPointUseCase,
    GetBonusPointsUseCase,
    RestoreBonusPointUseCase,
    UpdateBonusPointUseCase,
)
from app.bonus_point.deps import (
    get_bonus_points_uc,
    get_create_bonus_points_uc,
    get_delete_bonus_point_uc,
    get_restore_bonus_point_uc,
    get_update_bonus_point_uc,
)
from app.core.deps import hasPermission, hasTeamLeaderAccess
from app.core.permissions import BonusPointPermission
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/bonus-points", tags=["bonus-points"])


@router.get(
    "",
    response_model=ApiResponse[list[BonusPointResponse]],
    dependencies=[hasPermission(BonusPointPermission.READ)],
)
async def get_bonus_points(
    uc: Annotated[GetBonusPointsUseCase, Depends(get_bonus_points_uc)],
    user_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
):
    """Retrieve bonus points based on filters."""
    result = uc.execute(
        user_id=user_id, month=month, year=year, skip=skip, limit=limit, deleted=deleted
    )
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[list[BonusPointResponse]],
    dependencies=[
        hasPermission(BonusPointPermission.CREATE),
        hasTeamLeaderAccess("user_ids"),
    ],
)
async def create_bonus_point(
    data: BonusPointCreate,
    uc: Annotated[CreateBonusPointsUseCase, Depends(get_create_bonus_points_uc)],
):
    """Create new bonus point items."""
    result = uc.execute(data)
    return ApiResponse.success(data=result)


@router.put(
    "/{item_id}",
    response_model=ApiResponse[BonusPointResponse],
    dependencies=[
        hasPermission(BonusPointPermission.UPDATE),
        hasTeamLeaderAccess("user_id"),
    ],
)
async def update_bonus_point(
    item_id: int,
    data: BonusPointUpdate,
    uc: Annotated[UpdateBonusPointUseCase, Depends(get_update_bonus_point_uc)],
):
    """Update a bonus point item."""
    result = uc.execute(item_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return ApiResponse.success(data=result)


@router.delete(
    "/{item_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(BonusPointPermission.DELETE)],
)
async def delete_bonus_point(
    item_id: int,
    uc: Annotated[DeleteBonusPointUseCase, Depends(get_delete_bonus_point_uc)],
):
    """Delete a bonus point item."""
    result = uc.execute(item_id)
    return ApiResponse.success(data=result)


@router.put(
    "/{item_id}/restore",
    response_model=ApiResponse[BonusPointResponse],
    dependencies=[hasPermission(BonusPointPermission.DELETE)],
)
async def restore_bonus_point(
    item_id: int,
    uc: Annotated[RestoreBonusPointUseCase, Depends(get_restore_bonus_point_uc)],
):
    """Restore a deleted bonus point item."""
    result = uc.execute(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    return ApiResponse.success(data=result)
