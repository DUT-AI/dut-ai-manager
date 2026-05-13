from datetime import datetime
from typing import Annotated, List, Optional

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import HomeworkPermission, HomeworkSubmissionPermission
from app.homework.application.dtos import (
    HomeworkCreate,
    HomeworkReportResponse,
    HomeworkResponse,
    HomeworkSubmissionResponse,
    HomeworkUpdate,
)
from app.homework.application.use_cases import HomeworkUseCases
from app.homework.domain.value_objects import HomeworkStatus
from app.shared.application.response import ApiResponse
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Query
from dishka.integrations.fastapi import FromDishka, inject

router = APIRouter(prefix="/homeworks", tags=["homeworks"])
submission_router = APIRouter(prefix="/homework-submission", tags=["homework-submission"])


@router.get(
    "",
    response_model=ApiResponse[List[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_all_homeworks(
    use_cases: FromDishka[HomeworkUseCases],
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
@inject
async def get_my_homeworks(
    current_user: CurrentUser,
    use_cases: FromDishka[HomeworkUseCases],
    skip: int = 0,
    limit: int = 100,
):
    """Get homeworks assigned to the current user"""
    assert current_user.id is not None
    result = use_cases.get_assigned_to_user(current_user.id, skip=skip, limit=limit)
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
@inject
async def create_homework(
    use_cases: FromDishka[HomeworkUseCases],
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
    "/report/unsubmitted",
    response_model=ApiResponse[List[HomeworkReportResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_report(
    use_cases: FromDishka[HomeworkUseCases],
):
    """Báo cáo bài tập chưa nộp của tất cả active user"""
    result = use_cases.get_unsubmitted_report()
    return ApiResponse.success(data=result)


@router.get(
    "/report/unsubmitted/{user_id}",
    response_model=ApiResponse[List[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_by_user(
    user_id: int,
    use_cases: FromDishka[HomeworkUseCases],
):
    """Lấy danh sách bài tập chưa nộp của một user cụ thể"""
    result = use_cases.get_unsubmitted_by_user(user_id)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
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
@inject
async def update_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
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
@inject
async def delete_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
):
    result = use_cases.delete(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


@router.put("/{homework_id}/restore", response_model=ApiResponse[HomeworkResponse])
@inject
async def restore_homework(
    homework_id: int,
    use_cases: FromDishka[HomeworkUseCases],
    _current_user: Annotated[CurrentUser, hasPermission(HomeworkPermission.DELETE)],
):
    result = use_cases.restore(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found or not deleted")
    return ApiResponse.success(data=result)


# --- Submission Routes ---


@submission_router.post(
    "",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.CREATE)],
)
@inject
async def submit_homework(
    use_cases: FromDishka[HomeworkUseCases],
    homework_id: int = Form(..., description="ID của bài tập"),
    file: UploadFile = File(
        ..., description="File nén bài tập (.zip, .rar, .7z, .tar.gz)"
    ),
):
    """Submit homework by uploading a compressed file."""
    result = await use_cases.submit_homework(homework_id, file)
    return ApiResponse.success(data=result)


@submission_router.get(
    "",
    response_model=ApiResponse[List[HomeworkSubmissionResponse]],
    dependencies=[hasPermission(HomeworkSubmissionPermission.READ)],
)
@inject
async def get_submissions(
    current_user: CurrentUser,
    use_cases: FromDishka[HomeworkUseCases],
    homework_id: int = Query(..., description="ID của bài tập để lấy danh sách bài nộp"),
):
    """Lấy danh sách các bài nộp của một bài tập cụ thể"""
    result = use_cases.get_all_submissions_by_homework(homework_id, current_user)
    return ApiResponse.success(data=result)


@submission_router.get(
    "/me",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.READ)],
)
@inject
async def get_my_submission(
    use_cases: FromDishka[HomeworkUseCases],
    homework_id: int = Query(..., description="ID của bài tập"),
):
    """Lấy bài nộp cá nhân của bài tập này"""
    result = use_cases.get_submission_of_user(homework_id)
    return ApiResponse.success(data=result)


@submission_router.put(
    "/{submission_id}/status",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.UPDATE)],
)
@inject
async def update_submission_status(
    submission_id: int,
    status: HomeworkStatus,
    current_user: CurrentUser,
    use_cases: FromDishka[HomeworkUseCases],
):
    result = use_cases.update_submission_status(submission_id, status, current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Submission not found")
    return ApiResponse.success(data=result)
