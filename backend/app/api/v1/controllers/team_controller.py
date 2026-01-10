from app.core.permissions import TeamPermission
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.core.deps import ServiceFactoryDI, CurrentUser, hasPermission
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get(
    "",
    response_model=ApiResponse[List[TeamResponse]],
    dependencies=[hasPermission(TeamPermission.READ)],
)
async def get_teams(service_factory: ServiceFactoryDI, skip: int = 0, limit: int = 100):
    result = service_factory.team.get_all(skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.get(
    "/{team_id}",
    response_model=ApiResponse[TeamResponse],
    dependencies=[hasPermission(TeamPermission.READ)],
)
async def get_team(
    team_id: int,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.team.get_by_id(team_id)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[TeamResponse],
    dependencies=[hasPermission(TeamPermission.CREATE)],
)
async def create_team(data: TeamCreate, service_factory: ServiceFactoryDI):
    result = service_factory.team.create(data)
    return ApiResponse.success(data=result)


@router.put(
    "/{team_id}",
    response_model=ApiResponse[TeamResponse],
    dependencies=[hasPermission(TeamPermission.UPDATE)],
)
async def update_team(
    team_id: int,
    data: TeamUpdate,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.team.update(team_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return ApiResponse.success(data=result)


@router.delete(
    "/{team_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(TeamPermission.DELETE)],
)
async def delete_team(team_id: int, service_factory: ServiceFactoryDI):
    result = service_factory.team.delete(team_id)
    return ApiResponse.success(data=result)
