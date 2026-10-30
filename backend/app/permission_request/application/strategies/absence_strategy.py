from fastapi import HTTPException

from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.application.strategies.base import PermissionStrategy
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import AbsencePayload
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository


class AbsenceStrategy(PermissionStrategy[AbsencePayload]):
    """Chiến lược xử lý đơn xin vắng buổi sinh hoạt (ABSENCE)."""

    def __init__(
        self,
        permission_repo: PermissionRequestRepository,
        meeting_repo: MeetingRepository,
    ):
        self.permission_repo = permission_repo
        self.meeting_repo = meeting_repo

    @property
    def category(self) -> RequestCategory:
        return RequestCategory.ABSENCE

    def validate(self, request: PermissionRequest[AbsencePayload]) -> None:
        if not request.payload.meeting_id:
            raise HTTPException(
                status_code=400, detail="Vui lòng chọn buổi sinh hoạt cần xin vắng"
            )
        meeting = self.meeting_repo.get_by_id(request.payload.meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Không tìm thấy buổi sinh hoạt")

    async def on_created(
        self, request: PermissionRequest[AbsencePayload], user_id: int
    ) -> None:
        if request.payload.meeting_id and user_id:
            self.permission_repo.mark_participant_excused(
                request.payload.meeting_id, user_id
            )

    def on_deleted(
        self, request: PermissionRequest[AbsencePayload], user_id: int
    ) -> None:
        if request.payload.meeting_id and user_id:
            self.permission_repo.revert_participant_excused(
                request.payload.meeting_id, user_id
            )
