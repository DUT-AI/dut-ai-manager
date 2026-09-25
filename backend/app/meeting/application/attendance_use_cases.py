"""
Meeting Attendance & Status Use Cases — application layer.

Handles 23:59 daily job meeting attendance checking by evaluating participant
check-in states and publishing domain events to EventBus for decoupled violation handling.
"""

from datetime import date, datetime
from typing import cast

from fastapi import status

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.events import (
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.utils.datetime import get_current_utc7_time


class CheckMeetingAttendanceUseCase:
    """
    Kiểm tra điểm danh các buổi họp lúc 23:59 hàng ngày.
    Đánh giá trạng thái tham dự và phát tán Domain Events (ParticipantAbsenceRecorded, ParticipantLateRecorded).
    Việc xử lý vi phạm do Violation Domain tự động tiếp nhận và quyết định qua EventBus.
    """

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo
        self.event_bus = event_bus

    async def execute(self, target_date: date | None = None) -> int:
        if target_date is None:
            now = get_current_utc7_time()
            target_date = now.date()

        meetings = self.meeting_repo.get_by_date(target_date)
        if not meetings:
            return 0

        active_meetings = [m for m in meetings if m.require_check_in]
        if not active_meetings:
            return 0

        events_published_count = 0
        date_str = str(target_date)

        for meeting in active_meetings:
            m_id = meeting.id or 0
            for participant in meeting.participants:
                user_id = participant.user_id

                # Trường hợp A: Không check-in
                if participant.check_in_at is None:
                    await self.event_bus.publish(
                        cast(
                            DomainEvent,
                            ParticipantAbsenceRecorded(
                                user_id=user_id,
                                meeting_id=m_id,
                                meeting_title=meeting.title,
                                meeting_date=date_str,
                            ),
                        )
                    )
                    events_published_count += 1

                # Trường hợp B: Đã check-in
                else:
                    if participant.check_out_at is None:
                        participant.check_out_at = meeting.end_time

                    is_late = meeting.is_late(participant.check_in_at)
                    if not is_late:
                        participant.status = ParticipantStatus.COMPLETED
                        self.participant_repo.save(participant)
                    else:
                        await self.event_bus.publish(
                            cast(
                                DomainEvent,
                                ParticipantLateRecorded(
                                    user_id=user_id,
                                    meeting_id=m_id,
                                    meeting_title=meeting.title,
                                    check_in_at=participant.check_in_at,
                                    start_time=meeting.start_time,
                                ),
                            )
                        )
                        events_published_count += 1

        return events_published_count


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
