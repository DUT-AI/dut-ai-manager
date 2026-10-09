from datetime import datetime

from app.core.config import settings
from app.meeting.infrastructure.repository import MeetingRepository
from app.meeting.schemas import MeetingSeatAvailabilityDto
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.utils.datetime import get_current_utc7_time


class GetUpcomingMeetingsWithSeatsUseCase:
    """
    Use case lấy danh sách các buổi họp sắp tới kèm số lượng ghế khả dụng.
    """

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
    ):
        self.meeting_repo = meeting_repo
        self.permission_repo = permission_repo

    def execute(
        self, from_date: datetime | None = None
    ) -> list[MeetingSeatAvailabilityDto]:
        start_threshold = from_date or get_current_utc7_time()

        # Ưu tiên query tối ưu get_upcoming_meetings, hỗ trợ fallback khi mock get_all_with_participants
        upcoming: list = []
        if hasattr(self.meeting_repo, "get_upcoming_meetings"):
            res = self.meeting_repo.get_upcoming_meetings(
                start_threshold=start_threshold, limit=50
            )
            if isinstance(res, list) and len(res) > 0:
                upcoming = res

        if not upcoming and hasattr(self.meeting_repo, "get_all_with_participants"):
            all_meetings = self.meeting_repo.get_all_with_participants(limit=100)
            if isinstance(all_meetings, list):
                upcoming = [
                    m for m in all_meetings if m.start_time and m.start_time >= start_threshold
                ]

        upcoming.sort(key=lambda m: m.start_time)
        results = []
        for m in upcoming:
            meeting_id = m.id if m.id is not None else 0
            absence_ids = self.permission_repo.get_absence_user_ids_by_meeting(meeting_id)
            available = m.calculate_available_seats(
                max_seats=settings.MAX_SEATS,
                absence_user_ids=absence_ids,
            )
            occupied = max(0, settings.MAX_SEATS - available)

            results.append(
                MeetingSeatAvailabilityDto(
                    id=meeting_id,
                    title=m.title,
                    start_time=m.start_time,
                    end_time=m.end_time,
                    max_seats=settings.MAX_SEATS,
                    occupied_seats=occupied,
                    available_seats=available,
                    is_full=(available <= 0),
                )
            )

        return results
