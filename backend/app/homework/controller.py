from datetime import datetime
from typing import List, Optional

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import (HomeworkPermission,
                                  HomeworkSubmissionPermission)
from app.homework.application.dtos import (HomeworkCreate, HomeworkResponse,
                                           HomeworkSubmissionResponse,
                                           HomeworkUpdate)
from app.homework.application.use_cases import HomeworkUseCases
from app.homework.deps import get_homework_use_cases
from app.homework.domain.value_objects import HomeworkStatus
from app.schemas.response import ApiResponse
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

router = APIRouter(prefix="/homeworks", tags=["homeworks"])


@router.get(
    "",
    response_model=ApiResponse[List[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
async def get_all_homeworks(
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
):
    result = use_cases.get_all(skip=skip, limit=limit, deleted=deleted)
    return ApiResponse.success(data=result)


@router.get(
    "/me",
    response_model=ApiResponse[List[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
async def get_my_homeworks(
    current_user: CurrentUser,
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
    skip: int = 0,
    limit: int = 100,
):
    """Get homeworks assigned to the current user"""
    result = use_cases.get_assigned_to_user(current_user.id, skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
async def create_homework(
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
    title: str = Form(...),
    description: str = Form(""),
    deadline: str = Form(...),
    assignee_ids: Optional[List[int]] = Form(None),
    team_ids: Optional[List[int]] = Form(None),
    file: Optional[UploadFile] = File(None),
):
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
    )

    result = await use_cases.create(data, file)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
async def get_homework(
    homework_id: int,
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
):
    result = use_cases.get_by_id(homework_id)
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
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    deadline: Optional[str] = Form(None),
    assignee_ids: Optional[List[int]] = Form(None),
    team_ids: Optional[List[int]] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid deadline format")

    data = HomeworkUpdate(
        title=title,
        description=description,
        deadline=deadline_dt,
        assignee_ids=assignee_ids,
        team_ids=team_ids,
    )

    result = await use_cases.update(homework_id, data, file)
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
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
):
    result = use_cases.delete(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


# --- Submission Routes ---


@router.post(
    "/{homework_id}/submit",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.CREATE)],
)
async def submit_homework(
    homework_id: int,
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
    file: UploadFile = File(
        ..., description="File nén bài tập (.zip, .rar, .7z, .tar.gz)"
    ),
):
    """Submit homework by uploading a compressed file."""
    result = await use_cases.submit_homework(homework_id, file)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}/submissions",
    response_model=ApiResponse[List[HomeworkSubmissionResponse]],
    dependencies=[hasPermission(HomeworkSubmissionPermission.READ)],
)
async def get_submissions(
    homework_id: int,
    current_user: CurrentUser,
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
):
    result = use_cases.get_all_submissions_by_homework(homework_id, current_user)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}/my-submission",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.READ)],
)
async def get_my_submission(
    homework_id: int,
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
):
    result = use_cases.get_submission_of_user(homework_id)
    return ApiResponse.success(data=result)


@router.put(
    "/submissions/{submission_id}/status",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.UPDATE)],
)
async def update_submission_status(
    submission_id: int,
    status: HomeworkStatus,
    current_user: CurrentUser,
    use_cases: HomeworkUseCases = Depends(get_homework_use_cases),
):
    result = use_cases.update_submission_status(submission_id, status, current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Submission not found")
    return ApiResponse.success(data=result)
