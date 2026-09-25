from datetime import datetime
from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Query

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import HomeworkPermission
from app.homework.application import (
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworkSubmissionStatusUseCase,
    GetHomeworksUseCase,
    RescanAllHomeworksUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.dtos import (
    HomeworkCreate,
    HomeworkReportResponse,
    HomeworkResponse,
    HomeworkSubmissionStatusResponse,
    HomeworkUpdate,
)
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/homeworks", tags=["homeworks"])


@router.get(
    "",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_all_homeworks(
    get_homeworks_uc: FromDishka[GetHomeworksUseCase],
    skip: int = 0,
    limit: int = 100,
    deleted: bool = False,
):
    result = get_homeworks_uc.get_all(skip=skip, limit=limit, deleted=deleted)
    return ApiResponse.success(data=result)


@router.post(
    "/admin/rescan-all",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
@inject
async def rescan_all_homeworks(
    rescan_use_case: FromDishka[RescanAllHomeworksUseCase],
    dry_run: bool = Query(False, description="Chạy thử nghiệm không lưu DB"),
):
    """Admin API: Quét lại toàn bộ bài tập (cũ & mới) và tạo lại vi phạm chuẩn"""
    count = await rescan_use_case.execute(auto_sync_legacy=not dry_run)
    return ApiResponse.success(
        data={"message": "Rescan completed", "violations_processed": count, "dry_run": dry_run}
    )


@router.get(
    "/me",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_my_homeworks(
    current_user: CurrentUser,
    get_homeworks_uc: FromDishka[GetHomeworksUseCase],
    skip: int = 0,
    limit: int = 100,
):
    """Get homeworks assigned to the current user"""
    assert current_user.id is not None
    result = await get_homeworks_uc.get_assigned_to_user(
        current_user.id, skip=skip, limit=limit
    )
    return ApiResponse.success(data=result)


@router.post(
    "",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
@inject
async def create_homework(
    data: HomeworkCreate,
    create_uc: FromDishka[CreateHomeworkUseCase],
):
    deadline_ts = data.deadline.timestamp()
    now_ts = (
        datetime.now(data.deadline.tzinfo).timestamp()
        if data.deadline.tzinfo
        else datetime.now().timestamp()
    )
    if deadline_ts < now_ts:
        raise HTTPException(status_code=400, detail="Hạn nộp không được ở trong quá khứ")

    result = await create_uc.execute(data)
    return ApiResponse.success(data=result)


@router.get(
    "/report/unsubmitted",
    response_model=ApiResponse[list[HomeworkReportResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_report(
    get_homeworks_uc: FromDishka[GetHomeworksUseCase],
):
    """Lấy danh sách thống kê số bài tập chưa nộp của toàn bộ user"""
    result = await get_homeworks_uc.get_unsubmitted_report()
    return ApiResponse.success(data=result)


@router.get(
    "/report/unsubmitted/{user_id}",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_by_user(
    user_id: int,
    get_homeworks_uc: FromDishka[GetHomeworksUseCase],
):
    """Lấy danh sách bài tập chưa nộp của một user cụ thể"""
    result = await get_homeworks_uc.get_unsubmitted_for_user(user_id)
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}/submission-status",
    response_model=ApiResponse[HomeworkSubmissionStatusResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_homework_submission_status(
    homework_id: int,
    submission_status_uc: FromDishka[GetHomeworkSubmissionStatusUseCase],
):
    """Lấy danh sách người đã nộp / chưa nộp của một bài tập cụ thể"""
    result = await submission_status_uc.execute(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


@router.get(
    "/{homework_id}",
    response_model=ApiResponse[HomeworkResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_homework(
    homework_id: int,
    get_homeworks_uc: FromDishka[GetHomeworksUseCase],
):
    result = get_homeworks_uc.get_by_id(homework_id)
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
    data: HomeworkUpdate,
    update_uc: FromDishka[UpdateHomeworkUseCase],
):
    if data.deadline is not None:
        deadline_ts = data.deadline.timestamp()
        now_ts = (
            datetime.now(data.deadline.tzinfo).timestamp()
            if data.deadline.tzinfo
            else datetime.now().timestamp()
        )
        if deadline_ts < now_ts:
            raise HTTPException(status_code=400, detail="Hạn nộp không được ở trong quá khứ")

    result = await update_uc.execute(homework_id, data)
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
    delete_uc: FromDishka[DeleteHomeworkUseCase],
):
    result = delete_uc.execute(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    return ApiResponse.success(data=result)


@router.put("/{homework_id}/restore", response_model=ApiResponse[HomeworkResponse])
@inject
async def restore_homework(
    homework_id: int,
    homework_repo: FromDishka[HomeworkRepository],
    _current_user: Annotated[CurrentUser, hasPermission(HomeworkPermission.DELETE)],
):
    result = homework_repo.restore(homework_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found or not deleted")
    return ApiResponse.success(data=result)
