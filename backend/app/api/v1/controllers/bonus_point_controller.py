from typing import Annotated

from app.core.deps import ServiceFactoryDI, hasPermission, hasTeamLeaderAccess
from app.core.permissions import BonusPointPermission
from app.schemas.activity import BonusPointCreate, BonusPointResponse, BonusPointUpdate
from app.schemas.response import ApiResponse
from fastapi import APIRouter

router = APIRouter(prefix="/bonus-points", tags=["bonus-points"])


# --- Bonus Points CRUD ---
@router.get(
    "",
    response_model=ApiResponse[list[BonusPointResponse]],
    dependencies=[hasPermission(BonusPointPermission.READ)],
)
async def get_bonus_points(
    service_factory: ServiceFactoryDI,
    user_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    if user_id:
        result = service_factory.bonus_point.get_by_user_id(
            user_id, month=month, year=year
        )
    else:
        result = service_factory.bonus_point.get_all(skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[BonusPointResponse],
    dependencies=[
        hasPermission(BonusPointPermission.CREATE),
        hasTeamLeaderAccess("user_id"),
    ],
)
async def create_bonus_point(
    data: BonusPointCreate,
    service_factory: ServiceFactoryDI,
):
    item = service_factory.bonus_point.create(data)
    return ApiResponse.success(data=item)


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
    service_factory: ServiceFactoryDI,
):
    result = service_factory.bonus_point.update(item_id, data)
    return ApiResponse.success(data=result)


@router.delete(
    "/{item_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(BonusPointPermission.DELETE)],
)
async def delete_bonus_point(
    item_id: int,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.bonus_point.delete(item_id)
    return ApiResponse.success(data=result)
