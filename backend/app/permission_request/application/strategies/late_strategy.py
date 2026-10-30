from datetime import UTC, datetime

from fastapi import HTTPException

from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.application.strategies.base import PermissionStrategy
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import LatePayload
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.domain.datetime_types import ensure_utc


class LateStrategy(PermissionStrategy[LatePayload]):
    """Chiến lược xử lý đơn xin đi trễ buổi sinh hoạt (LATE)."""

    def __init__(
        self,
        permission_repo: PermissionRequestRepository,
        meeting_repo: MeetingRepository,
    ):
        self.permission_repo = permission_repo
        self.meeting_repo = meeting_repo

    @property
    def category(self) -> RequestCategory:
        return RequestCategory.LATE

    def validate(
        self,
        request: PermissionRequest[LatePayload],
        now: datetime | None = None,
    ) -> None:
        meeting_id = request.payload.meeting_id
        arrival_time = ensure_utc(request.payload.start_time)

        if not meeting_id:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn buổi sinh hoạt cần xin đi trễ",
            )
        if not arrival_time:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn thời gian dự kiến đến buổi sinh hoạt",
            )

        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Không tìm thấy buổi sinh hoạt")

        current_time = ensure_utc(now) if now else datetime.now(UTC)
        meeting_start = ensure_utc(meeting.start_time)
        meeting_end = ensure_utc(meeting.end_time)

        if current_time >= meeting_end:
            raise HTTPException(
                status_code=400,
                detail="Không thể xin đi trễ cho buổi sinh hoạt đã kết thúc",
            )

        if arrival_time <= meeting_start:
            raise HTTPException(
                status_code=400,
                detail="Thời gian dự kiến đến phải sau giờ bắt đầu của buổi sinh hoạt",
            )

        if arrival_time > meeting_end:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Thời gian dự kiến đến không được vượt quá lúc kết thúc buổi họp"
                ),
            )

    async def on_created(
        self, request: PermissionRequest[LatePayload], user_id: int
    ) -> None:
        if request.payload.meeting_id and user_id:
            self.permission_repo.mark_participant_late_excused(
                request.payload.meeting_id, user_id
            )

    def on_deleted(self, request: PermissionRequest[LatePayload], user_id: int) -> None:
        if request.payload.meeting_id and user_id:
            self.permission_repo.revert_participant_excused(
                request.payload.meeting_id, user_id
            )
