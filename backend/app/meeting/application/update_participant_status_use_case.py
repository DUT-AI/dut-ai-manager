from datetime import datetime

from fastapi import status

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException


class UpdateParticipantStatusUseCase:
    """Cập nhật thủ công trạng thái của thành viên trong meeting (người tạo meeting / Admin)"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
    ):
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo

    def execute(
        self,
        meeting_id: int,
        user_id: int,
        target_status: ParticipantStatus,
        check_in_at: datetime | None = None,
        check_out_at: datetime | None = None,
    ) -> MeetingParticipant:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException(
                "Không tìm thấy buổi họp", status_code=status.HTTP_404_NOT_FOUND
            )

        if check_in_at is None and target_status in (
            ParticipantStatus.JOINED,
            ParticipantStatus.LATE_EXCUSED,
            ParticipantStatus.LATE_UNEXCUSED,
            ParticipantStatus.COMPLETED,
        ):
            check_in_at = meeting.start_time

        if check_out_at is None and target_status == ParticipantStatus.COMPLETED:
            check_out_at = meeting.end_time

        updated = self.participant_repo.update_participant_status(
            meeting_id=meeting_id,
            user_id=user_id,
            status=target_status,
            check_in_at=check_in_at,
            check_out_at=check_out_at,
        )
        return updated
