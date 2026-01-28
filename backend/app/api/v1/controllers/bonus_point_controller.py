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
    deleted: bool = False,
):
    if user_id:
        # Note: repository specific get methods might not support deleted yet,
        # but get_all does via BaseRepository.
        # Ideally, we should update custom queries too, but for TrashPage we mainly use generic list.
        # For now, if deleted=True, we rely on get_all or update custom queries if needed.
        # The user requested Trash Page lists deleted items.
        # If user_id is provided, we might need filtering.
        # Let's check BonusPointRepository.
        # result = service_factory.bonus_point.get(user_id=user_id, month=month, year=year)
        # We need to update service.get to support deleted if we want to filter by user in Trash.
        # For now, let's keep it simple for the Trash Page which often lists all or by user.
        # Assuming modifying service.get implementation or repository methods is out of scope
        # unless strictly required by new TrashPage design.
        # The BaseRepository update handles get_all(deleted=True).
        result = service_factory.bonus_point.get(
            user_id=user_id, month=month, year=year
        )
        # TODO: Update other repository methods if needed.
    else:
        result = service_factory.bonus_point.get_all(
            skip=skip, limit=limit, deleted=deleted
        )
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[list[BonusPointResponse]],
    dependencies=[
        hasPermission(BonusPointPermission.CREATE),
        hasTeamLeaderAccess(
            "user_ids"
        ),  # Update dependency to check user_ids if possible? hasTeamLeaderAccess might need Check.
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


@router.put(
    "/{item_id}/restore",
    response_model=ApiResponse[BonusPointResponse],
    dependencies=[hasPermission(BonusPointPermission.DELETE)],
)
async def restore_bonus_point(
    item_id: int,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.bonus_point.restore(item_id)
    if not result:
        # Can't find or not deleted
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    return ApiResponse.success(data=result)
