from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import hasPermission
from app.core.permissions import TeamPermission
from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta
from app.team.application.dtos import (
    TeamCreate,
    TeamOptionDto,
    TeamResponse,
    TeamUpdate,
)
from app.team.application.use_cases import TeamUseCases

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get(
    "",
    response_model=ApiResponse[list[TeamResponse]],
    dependencies=[hasPermission(TeamPermission.READ)],
)
@inject
async def get_teams(
    usecases: FromDishka[TeamUseCases],
    pagination: Annotated[PaginationParams, Depends()],
):
    teams, total = usecases.get_paged(
        page=pagination.page, page_size=pagination.page_size
    )
    meta = PaginationMeta.create(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
    return ApiResponse.success(data=teams, pagination=meta)


@router.get(
    "/options",
    response_model=ApiResponse[list[TeamOptionDto]],
    dependencies=[hasPermission(TeamPermission.READ)],
)
@inject
async def get_team_options(
    usecases: FromDishka[TeamUseCases],
):
    """Get lightweight list of teams for select dropdowns."""
    teams = usecases.get_all(skip=0, limit=1000)
    return ApiResponse.success(
        data=[
            TeamOptionDto(id=t.id, name=t.team_name) for t in teams if t.id is not None
        ],
        message="Fetched team options successfully",
    )


@router.get(
    "/{team_id}",
    response_model=ApiResponse[TeamResponse],
    dependencies=[hasPermission(TeamPermission.READ)],
)
@inject
async def get_team(
    team_id: int,
    usecases: FromDishka[TeamUseCases],
):
    result = usecases.get_by_id(team_id)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[TeamResponse],
    dependencies=[hasPermission(TeamPermission.CREATE)],
)
@inject
async def create_team(
    data: TeamCreate,
    usecases: FromDishka[TeamUseCases],
):
    result = usecases.create(data)
    return ApiResponse.success(data=result)


@router.put(
    "/{team_id}",
    response_model=ApiResponse[TeamResponse],
    dependencies=[hasPermission(TeamPermission.UPDATE)],
)
@inject
async def update_team(
    team_id: int,
    data: TeamUpdate,
    usecases: FromDishka[TeamUseCases],
):
    result = usecases.update(team_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return ApiResponse.success(data=result)


@router.delete(
    "/{team_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(TeamPermission.DELETE)],
)
@inject
async def delete_team(
    team_id: int,
    usecases: FromDishka[TeamUseCases],
):
    result = usecases.delete(team_id)
    return ApiResponse.success(data=result)
