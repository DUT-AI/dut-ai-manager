from fastapi import HTTPException

from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.permission_request.application.strategies.base import PermissionStrategy
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import PostponePayload
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.datetime_types import ensure_utc


class PostponeStrategy(PermissionStrategy[PostponePayload]):
    """Chiến lược xử lý đơn xin hoãn nộp bài tập (POSTPONE)."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    @property
    def category(self) -> RequestCategory:
        return RequestCategory.POSTPONE

    def validate(self, request: PermissionRequest[PostponePayload]) -> None:
        homework_id = request.payload.homework_id
        extended_deadline = ensure_utc(request.payload.start_time)

        if not homework_id:
            raise HTTPException(
                status_code=400, detail="Vui lòng chọn bài tập cần hoãn"
            )

        homework = self.homework_repo.get_by_id(homework_id)
        if not homework:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")

        delta = extended_deadline - ensure_utc(homework.deadline)
        if delta.total_seconds() > 4 * 24 * 3600:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Thời gian xin hoãn không được vượt quá 4 ngày so với deadline gốc"
                ),
            )
        if delta.total_seconds() < 0:
            raise HTTPException(
                status_code=400, detail="Thời gian gia hạn mới phải sau deadline gốc"
            )

    async def on_created(
        self, request: PermissionRequest[PostponePayload], user_id: int
    ) -> None:
        # Không có side-effects tức thì đối với bài tập
        pass

    def on_deleted(
        self, request: PermissionRequest[PostponePayload], user_id: int
    ) -> None:
        pass
