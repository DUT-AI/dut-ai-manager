from typing import Annotated, List

from app.core.deps import CurrentUser, ServiceFactoryDI, hasPermission
from app.core.permissions import HomeworkPermission
from app.models import HomeworkStatus, User
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkResponse,
    HomeworkSubmissionCreate,
    HomeworkSubmissionResponse,
    HomeworkSubmissionUpdate,
    HomeworkUpdate,
)
from app.schemas.response import ApiResponse
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/homeworks", tags=["homeworks"])


@router.get(
    "",
    response_model=ApiResponse[List[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
async def get_all_homeworks(
    service_factory: ServiceFactoryDI,
    skip: int = 0,
    limit: int = 100,
):
    result = service_factory.homework.get_all(skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.get(
    "/me",
    response_model=ApiResponse[List[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
async def get_my_homeworks(
    service_factory: ServiceFactoryDI,
    skip: int = 0,
    limit: int = 100,
):
    """Get homeworks assigned to the current user"""
    result = service_factory.homework.get_assigned_to_user(skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
async def create_homework(
    data: HomeworkCreate,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.homework.create(data)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
async def get_homework(
    homework_id: int,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.homework.get_by_id(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


@router.put(
    "/{homework_id}",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.UPDATE)],
)
async def update_homework(
    homework_id: int,
    data: HomeworkUpdate,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.homework.update(homework_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


@router.delete(
    "/{homework_id}",
    response_model=ApiResponse[bool],
    dependencies=[hasPermission(HomeworkPermission.DELETE)],
)
async def delete_homework(
    homework_id: int,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.homework.delete(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)
