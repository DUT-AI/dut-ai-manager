from app.core.deps import hasTeamLeaderAccess
from app.core.deps import CurrentUser
from app.core.permissions import HomeworkSubmissionPermission
from fastapi.exceptions import HTTPException
from app.models.homework_submission import HomeworkStatus
from typing import List
from app.core.deps import ServiceFactoryDI
from app.core.permissions import HomeworkPermission
from app.core.deps import hasPermission
from app.schemas.homework import HomeworkSubmissionCreate
from app.schemas.homework import HomeworkSubmissionResponse
from app.schemas.response import ApiResponse
from fastapi.routing import APIRouter

router = APIRouter(prefix="/homework-submissions", tags=["Homework Submissions"])


@router.post(
    "/{homework_id}/submit",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.CREATE)],
)
async def submit_homework(
    homework_id: int,
    data: HomeworkSubmissionCreate,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.homework_submission.submit(homework_id, data)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}/submissions",
    response_model=ApiResponse[List[HomeworkSubmissionResponse]],
    dependencies=[hasPermission(HomeworkSubmissionPermission.READ)],
)
async def get_submissions(
    homework_id: int,
    service_factory: ServiceFactoryDI,
    current_user: CurrentUser,
):
    result = service_factory.homework_submission.get_all_by_homework(
        homework_id, current_user
    )
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}/my-submission",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[hasPermission(HomeworkSubmissionPermission.READ)],
)
async def get_my_submission(
    homework_id: int,
    service_factory: ServiceFactoryDI,
):
    result = service_factory.homework_submission.get_submission_of_user(homework_id)
    return ApiResponse.success(data=result)


@router.put(
    "/submissions/{submission_id}/status",
    response_model=ApiResponse[HomeworkSubmissionResponse],
    dependencies=[
        hasPermission(HomeworkSubmissionPermission.UPDATE),
    ],
)
async def update_submission_status(
    submission_id: int,
    status: HomeworkStatus,
    service_factory: ServiceFactoryDI,
    current_user: CurrentUser,
):
    result = service_factory.homework_submission.update_status(
        submission_id, status, current_user
    )
    if not result:
        raise HTTPException(status_code=404, detail="Submission not found")
    return ApiResponse.success(data=result)
