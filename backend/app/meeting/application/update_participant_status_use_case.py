from datetime import datetime

from fastapi import status

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.utils.datetime import get_current_utc7_time, to_utc7_naive


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

        participant = self.participant_repo.get_by_meeting_and_user(
            meeting_id=meeting_id, user_id=user_id
        )
        if not participant:
            raise BadRequestException(
                f"Không tìm thấy thành viên {user_id} trong buổi họp",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Chuẩn hóa múi giờ sang UTC+7 naive datetime
        normalized_check_in_at = to_utc7_naive(check_in_at)
        normalized_check_out_at = to_utc7_naive(check_out_at)

        now_utc7 = get_current_utc7_time()
        # Default start time khi điểm danh nhanh là giờ hiện tại nếu đang trong buổi học, hoặc start_time
        default_check_in_time = (
            now_utc7
            if meeting.start_time <= now_utc7 <= meeting.end_time
            else meeting.start_time
        )

        # Ủy quyền toàn bộ Business Rules cho Domain Entity
        participant.update_attendance_status(
            new_status=target_status,
            check_in_at=normalized_check_in_at,
            check_out_at=normalized_check_out_at,
            default_start_time=default_check_in_time,
            default_end_time=meeting.end_time,
        )

        # Lưu Domain Entity vào Repository
        updated = self.participant_repo.update_participant_status(
            meeting_id=meeting_id,
            user_id=user_id,
            status=participant.status,
            check_in_at=participant.check_in_at,
            check_out_at=participant.check_out_at,
        )
        return updated
