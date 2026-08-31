from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException

from app.core.deps import hasPermission
from app.core.permissions import TeamPermission
from app.shared.application.response import ApiResponse
from app.team.application.dtos import (
    TeamCreate,
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
    skip: int = 0,
    limit: int = 100,
):
    result = usecases.get_all(skip=skip, limit=limit)
    return ApiResponse.success(data=result)


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
