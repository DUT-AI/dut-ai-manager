from typing import Annotated, Any, Literal

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.core.config import settings
from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import HomeworkPermission
from app.homework.application import (
    BackfillHomeworkExercisesUseCase,
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworkDetailUseCase,
    GetHomeworksPagedUseCase,
    GetHomeworkSubmissionStatusUseCase,
    GetMyHomeworkDetailUseCase,
    GetUnsubmittedHomeworkReportUseCase,
    GetUnsubmittedHomeworksForUserUseCase,
    GetUserHomeworkSubmissionsUseCase,
    GetUserHomeworksUseCase,
    HomeworkSubmissionWebhookIn,
    RecordHomeworkSubmissionUseCase,
    RescanAllHomeworksUseCase,
    SyncHomeworkFromQuizUseCase,
    SyncMyUnsubmittedHomeworksUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.dtos import (
    BackfillHomeworkExercisesResult,
    HomeworkCreate,
    HomeworkReportResponse,
    HomeworkResponse,
    HomeworkResponseDetail,
    HomeworkSubmissionDetailResponse,
    HomeworkSubmissionStatusResponse,
    HomeworkUpdate,
    HomeworkWebhookResponse,
    MyHomeworkDetailResponse,
    MyHomeworksPageResponse,
    SyncHomeworkResult,
    SyncMyHomeworksResult,
)
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta

router = APIRouter(prefix="/homeworks", tags=["homeworks"])


@router.get(
    "",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_all_homeworks(
    get_paged_uc: FromDishka[GetHomeworksPagedUseCase],
    pagination: Annotated[PaginationParams, Depends()],
    deleted: bool = False,
):
    homeworks, total, deadlines = get_paged_uc.execute(
        page=pagination.page, page_size=pagination.page_size, deleted=deleted
    )
    meta = PaginationMeta.create(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
    return ApiResponse.success(
        data=[
            HomeworkResponse.from_domain(h, deadline=deadlines.get(h.id))
            for h in homeworks
        ],
        message="Homeworks retrieved successfully",
        pagination=meta,
    )


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


@router.post(
    "/admin/backfill-exercises",
    response_model=ApiResponse[BackfillHomeworkExercisesResult],
    dependencies=[hasPermission(HomeworkPermission.CREATE)],
)
@inject
async def backfill_homework_exercises(
    backfill_uc: FromDishka[BackfillHomeworkExercisesUseCase],
    sync_submissions: bool = Query(
        True, description="Đồng bộ kèm toàn bộ lượt nộp từ Quiz API"
    ),
):
    """Admin API: Chuẩn hóa danh mục bài tập con chính thức cho toàn bộ bài tập hiện có."""
    result = await backfill_uc.execute(sync_submissions=sync_submissions)
    return ApiResponse.success(
        data=result,
        message="Hoàn tất chuẩn hóa danh mục bài tập con.",
    )


@router.get(
    "/me",
    response_model=ApiResponse[MyHomeworksPageResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_my_homeworks(
    current_user: CurrentUser,
    get_user_homeworks_uc: FromDishka[GetUserHomeworksUseCase],
    pagination: Annotated[PaginationParams, Depends()],
    status: Literal["all", "uncompleted", "completed", "overdue"] = Query(
        "all", description="Lọc theo trạng thái hoàn thành / quá hạn"
    ),
    search: str | None = Query(None, description="Tìm kiếm theo tên bài tập"),
):
    """Lấy danh sách bài tập được giao cho học viên hiện tại (Server-driven filter, search, stats & pagination)."""
    result, total = await get_user_homeworks_uc.execute(
        current_user.user_id,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status,
        search=search,
    )
    meta = PaginationMeta.create(
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
    return ApiResponse.success(data=result, pagination=meta)


@router.post(
    "/me/sync",
    response_model=ApiResponse[SyncMyHomeworksResult],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def sync_my_unsubmitted_homeworks(
    current_user: CurrentUser,
    sync_my_uc: FromDishka[SyncMyUnsubmittedHomeworksUseCase],
):
    """Học viên chủ động đồng bộ nhanh các bài tập chưa hoàn thành của mình từ hệ thống Quiz."""
    result = await sync_my_uc.execute(current_user.user_id)
    message = (
        f"Đã đồng bộ {result.synced_count}/{result.total_checked} bài tập chưa hoàn thành từ Quiz."
        if result.total_checked > 0
        else "Tất cả bài tập của bạn đã được hoàn thành."
    )
    return ApiResponse.success(data=result, message=message)


@router.get(
    "/me/{homework_id}",
    response_model=ApiResponse[MyHomeworkDetailResponse],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_my_homework_detail(
    homework_id: int,
    current_user: CurrentUser,
    get_my_detail_uc: FromDishka[GetMyHomeworkDetailUseCase],
):
    """Lấy chi tiết bài tập cá nhân của học viên kèm hạn nộp cá nhân, tiến độ bài con và lịch sử nộp."""
    result = await get_my_detail_uc.execute(homework_id, current_user.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
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
    return ApiResponse.success(
        data=HomeworkResponse.from_entity(result, deadline=data.deadline)
    )


@router.get(
    "/report/unsubmitted",
    response_model=ApiResponse[list[HomeworkReportResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_report(
    get_report_uc: FromDishka[GetUnsubmittedHomeworkReportUseCase],
):
    """Lấy danh sách thống kê số bài tập chưa nộp của toàn bộ user"""
    result = await get_report_uc.execute()
    return ApiResponse.success(data=result)


@router.get(
    "/report/unsubmitted/{user_id}",
    response_model=ApiResponse[list[HomeworkResponse]],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_unsubmitted_by_user(
    user_id: int,
    get_unsubmitted_uc: FromDishka[GetUnsubmittedHomeworksForUserUseCase],
):
    """Lấy danh sách bài tập chưa nộp của một user cụ thể"""
    result = await get_unsubmitted_uc.execute(user_id)
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
    response_model=ApiResponse[HomeworkResponseDetail],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def get_homework(
    homework_id: int,
    get_detail_uc: FromDishka[GetHomeworkDetailUseCase],
):
    result = await get_detail_uc.execute(homework_id)
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
    homework_assignee_repo: FromDishka[HomeworkAssigneeRepository],
):
    result = await update_uc.execute(homework_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Homework not found")
    effective_dl = data.deadline
    if effective_dl is None and result.id:
        min_deadlines = homework_assignee_repo.get_min_deadlines_by_homework_ids(
            [result.id]
        )
        effective_dl = min_deadlines.get(result.id)
    return ApiResponse.success(
        data=HomeworkResponse.from_entity(result, deadline=effective_dl)
    )


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


@router.post("/webhook/submission", response_model=ApiResponse[HomeworkWebhookResponse])
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
    submissions = await use_case.execute(homework_id, current_user.user_id)
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
    response_model=ApiResponse[SyncHomeworkResult],
    dependencies=[hasPermission(HomeworkPermission.READ)],
)
@inject
async def sync_homework_from_quiz(
    homework_id: int,
    sync_uc: FromDishka[SyncHomeworkFromQuizUseCase],
):
    """
    Đồng bộ thủ công từ Quiz API về bảng homework_exercises & homework_submissions cho 1 bài tập.
    """
    result = await sync_uc.execute(homework_id)
    return ApiResponse.success(data=result)
