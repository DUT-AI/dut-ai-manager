from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import hasPermission
from app.core.permissions import TeamPermission
from app.shared.application.response import ApiResponse
from app.team.application.dtos import (
    TeamCreate,
    TeamResponse,
    TeamUpdate,
)
from app.team.application.use_cases import TeamUseCases
from app.team.deps import get_team_usecases

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get(
    "",
    response_model=ApiResponse[list[TeamResponse]],
    dependencies=[hasPermission(TeamPermission.READ)],
)
async def get_teams(
    usecases: TeamUseCases = Depends(get_team_usecases),
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
async def get_team(
    team_id: int,
    usecases: TeamUseCases = Depends(get_team_usecases),
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
async def create_team(
    data: TeamCreate,
    usecases: TeamUseCases = Depends(get_team_usecases),
):
    result = usecases.create(data)
    return ApiResponse.success(data=result)


@router.put(
    "/{team_id}",
    response_model=ApiResponse[TeamResponse],
    dependencies=[hasPermission(TeamPermission.UPDATE)],
)
async def update_team(
    team_id: int,
    data: TeamUpdate,
    usecases: TeamUseCases = Depends(get_team_usecases),
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
async def delete_team(
    team_id: int,
    usecases: TeamUseCases = Depends(get_team_usecases),
):
    result = usecases.delete(team_id)
    return ApiResponse.success(data=result)
