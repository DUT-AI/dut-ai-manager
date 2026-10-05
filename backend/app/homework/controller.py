from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import settings
from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import HomeworkPermission
from app.homework.application import (
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworkSubmissionStatusUseCase,
    GetHomeworksUseCase,
    GetUserHomeworkSubmissionsUseCase,
    HomeworkSubmissionWebhookIn,
    RecordHomeworkSubmissionUseCase,
    RescanAllHomeworksUseCase,
    SyncHomeworkFromQuizUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.dtos import (
    HomeworkCreate,
    HomeworkReportResponse,
    HomeworkResponse,
    HomeworkSubmissionDetailResponse,
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
        data={
            "message": "Rescan completed",
            "violations_processed": count,
            "dry_run": dry_run,
        }
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


@router.post("/webhook/submission", response_model=ApiResponse[dict[str, Any]])
@inject
async def receive_submission_webhook(
    payload: HomeworkSubmissionWebhookIn,
    record_uc: FromDishka[RecordHomeworkSubmissionUseCase],
    x_webhook_secret: Annotated[str | None, Header(alias="X-Webhook-Secret")] = None,
):
    """
    Webhook endpoint nhận sự kiện nộp bài (Coding / Game) từ hệ thống Quiz.
    Yêu cầu bảo mật: Header 'X-Webhook-Secret'.
    """
    if not x_webhook_secret or x_webhook_secret != settings.QUIZ_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Webhook-Secret header",
        )

    res = await record_uc.execute(payload)
    return ApiResponse.success(data=res)


@router.get(
    "/{homework_id}/my-submissions",
    response_model=ApiResponse[list[HomeworkSubmissionDetailResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_my_homework_submissions(
    homework_id: int,
    current_user: CurrentUser,
    use_case: FromDishka[GetUserHomeworkSubmissionsUseCase],
):
    """Lấy danh sách lịch sử tất cả các lần nộp bài (Audit log) của học viên đang đăng nhập."""
    assert current_user.id is not None
    submissions = await use_case.execute(homework_id, current_user.id)
    return ApiResponse.success(data=submissions)


@router.get(
    "/{homework_id}/users/{user_id}/submissions",
    response_model=ApiResponse[list[HomeworkSubmissionDetailResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_user_homework_submissions(
    homework_id: int,
    user_id: int,
    use_case: FromDishka[GetUserHomeworkSubmissionsUseCase],
):
    """Lấy danh sách lịch sử tất cả các lần nộp bài (Audit log) của 1 học viên."""
    submissions = await use_case.execute(homework_id, user_id)
    return ApiResponse.success(data=submissions)


@router.post(
    "/{homework_id}/sync",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
@inject
async def sync_homework_from_quiz(
    homework_id: int,
    sync_uc: FromDishka[SyncHomeworkFromQuizUseCase],
):
    """
    Đồng bộ thủ công từ Quiz API về bảng homework_submissions cho 1 bài tập.
    Hỗ trợ nút bấm 'Đồng bộ từ Quiz' trên giao diện quản trị.
    """
    result = await sync_uc.execute(homework_id)
    return ApiResponse.success(data=result)
