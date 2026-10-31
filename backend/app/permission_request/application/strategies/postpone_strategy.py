from datetime import UTC, datetime

from fastapi import HTTPException

from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.permission_request.application.strategies.base import PermissionStrategy
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import PostponePayload
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.datetime_types import ensure_utc


class PostponeStrategy(PermissionStrategy[PostponePayload]):
    """Chiến lược xử lý đơn xin hoãn nộp bài tập (POSTPONE)."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_submission_repo = homework_submission_repo

    @property
    def category(self) -> RequestCategory:
        return RequestCategory.POSTPONE

    def validate(self, request: PermissionRequest[PostponePayload]) -> None:
        homework_id = request.payload.homework_id
        extended_deadline = (
            ensure_utc(request.payload.start_time)
            if request.payload.start_time
            else None
        )

        if not homework_id:
            raise HTTPException(
                status_code=400, detail="Vui lòng chọn bài tập cần hoãn"
            )
        if not extended_deadline:
            raise HTTPException(
                status_code=400, detail="Vui lòng chọn thời gian gia hạn mới"
            )

        now_utc = datetime.now(UTC)
        if extended_deadline <= now_utc:
            raise HTTPException(
                status_code=400,
                detail="Thời gian gia hạn mới phải ở tương lai",
            )

        homework = self.homework_repo.get_by_id(homework_id)
        if not homework:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")

        uid = request.user_id
        if uid:
            current_deadline = self.homework_assignee_repo.get_user_deadline(
                homework_id, uid
            )
            if not current_deadline:
                raise HTTPException(
                    status_code=400,
                    detail="Bạn không được phân công bài tập này",
                )

            current_deadline_utc = ensure_utc(current_deadline)
            if current_deadline_utc <= now_utc:
                raise HTTPException(
                    status_code=400,
                    detail="Bài tập đã quá hạn, không thể tạo đơn xin hoãn",
                )

            # Chặn tạo đơn khi bài tập đã được hoàn thành trọn vẹn
            submissions = self.homework_submission_repo.get_submissions_by_user(
                homework_id, uid
            )
            if homework.evaluate_submissions(
                submissions, deadline=current_deadline_utc
            ).is_submitted:
                raise HTTPException(
                    status_code=400,
                    detail="Bạn đã hoàn thành bài tập này, không thể xin hoãn",
                )

            delta = extended_deadline - current_deadline_utc
            if delta.total_seconds() > 4 * 24 * 3600:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Thời gian xin hoãn không được vượt quá 4 ngày so với deadline hiện tại"
                    ),
                )
            if delta.total_seconds() <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Thời gian gia hạn mới phải sau deadline hiện tại",
                )

    async def on_created(
        self, request: PermissionRequest[PostponePayload], user_id: int
    ) -> None:
        hw_id = request.payload.homework_id
        new_dl = request.payload.start_time
        if hw_id and new_dl:
            current_dl = self.homework_assignee_repo.get_user_deadline(hw_id, user_id)
            if current_dl:
                request.payload = request.payload.model_copy(
                    update={"old_deadline": current_dl}
                )
            self.homework_assignee_repo.update_deadline(
                hw_id, user_id, ensure_utc(new_dl)
            )

    def on_deleted(
        self, request: PermissionRequest[PostponePayload], user_id: int
    ) -> None:
        hw_id = request.payload.homework_id
        old_dl = request.payload.old_deadline
        if hw_id and old_dl:
            self.homework_assignee_repo.update_deadline(
                hw_id, user_id, ensure_utc(old_dl)
            )
