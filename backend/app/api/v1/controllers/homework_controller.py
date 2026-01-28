from typing import List, Optional

from app.core.deps import CurrentUser, ServiceFactoryDI, hasPermission
from app.core.permissions import HomeworkPermission
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkResponse,
    HomeworkUpdate,
)
from app.schemas.response import ApiResponse
from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends

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
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """Get homeworks assigned to the current user"""
    result = service_factory.homework.get_assigned_to_user(
        current_user.id, skip=skip, limit=limit
    )
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
async def create_homework(
    service_factory: ServiceFactoryDI,
    title: str = Form(...),
    description: str = Form(""),
    deadline: str = Form(...),
    assignee_ids: Optional[List[int]] = Form(None),
    team_ids: Optional[List[int]] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    from app.core.minio_service import get_minio_service
    from datetime import datetime
    import uuid
    import os

    file_url = None
    if file:
        minio_service = get_minio_service()
        # Read content to validate size
        content = await file.read()
        error = minio_service.validate_file(file.filename, len(content))
        if error:
            raise HTTPException(status_code=400, detail=error)

        # Upload
        ext = os.path.splitext(file.filename)[1]
        filename = f"{minio_service.SUBMISSIONS_PREFIX}/{uuid.uuid4()}{ext}"
        try:
            file_url = minio_service.upload_file(content, filename, file.content_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # Parse deadline string to datetime
    try:
        deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deadline format")

    data = HomeworkCreate(
        title=title,
        description=description,
        deadline=deadline_dt,
        assignee_ids=assignee_ids,
        team_ids=team_ids,
        file_url=file_url,
    )

    result = await service_factory.homework.create(data)
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
    result = await service_factory.homework.update(homework_id, data)
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
