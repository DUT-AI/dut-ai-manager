from fastapi import HTTPException

from app.homework.application.dtos import HomeworkResponse
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.meeting.infrastructure.repository import MeetingRepository
from app.meeting.schemas import MeetingResponse
from app.permission_request.infrastructure.repository import (
    PermissionRequestRepository,
)
from app.permission_request.schemas import PermissionRequestDetailResponse


class GetPermissionRequestDetailUseCase:
    """Lấy chi tiết một yêu cầu xin phép (kèm quan hệ đầy đủ)."""

    def __init__(
        self,
        repo: PermissionRequestRepository,
        meeting_repo: MeetingRepository,
        homework_repo: HomeworkRepository,
    ):
        self.repo = repo
        self.meeting_repo = meeting_repo
        self.homework_repo = homework_repo

    def execute(self, request_id: int) -> PermissionRequestDetailResponse:
        row = self.repo.get_detail_by_id(request_id)
        if not row:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy yêu cầu xin phép"
            )

        entity = row.to_entity()

        meeting_dto = None
        if entity.meeting_id:
            meeting_entity = self.meeting_repo.get_by_id(entity.meeting_id)
            if meeting_entity:
                meeting_dto = MeetingResponse.model_validate(meeting_entity)

        old_meeting_dto = None
        if entity.old_meeting_id:
            old_meeting_entity = self.meeting_repo.get_by_id(entity.old_meeting_id)
            if old_meeting_entity:
                old_meeting_dto = MeetingResponse.model_validate(old_meeting_entity)

        homework_dto = None
        if entity.homework_id:
            homework_entity = self.homework_repo.get_by_id(entity.homework_id)
            if homework_entity:
                homework_dto = HomeworkResponse.model_validate(homework_entity)

        return PermissionRequestDetailResponse(
            id=entity.id,
            category=entity.category,
            note=entity.note,
            homework_id=entity.homework_id,
            meeting_id=entity.meeting_id,
            old_meeting_id=entity.old_meeting_id,
            start_time=entity.start_time,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            creator=entity.creator,
            updater=entity.updater,
            homework=homework_dto,
            meeting=meeting_dto,
            old_meeting=old_meeting_dto,
        )
