from datetime import date
from typing import cast

from app.meeting.domain.events import (
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
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
