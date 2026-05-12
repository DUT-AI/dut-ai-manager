"""
Capacity Use Cases

Chứa logic nghiệp vụ liên quan đến việc tính toán sức chứa của phòng lab.
"""

from datetime import timedelta

from app.meeting.domain.value_objects import CapacityMonitor
from app.meeting.infrastructure.repository import MeetingRepository
from app.utils.datetime import get_current_utc7_time


class CalculateCurrentCapacityUseCase:
    """Tính toán capacity hiện tại"""

    FORECAST_WINDOW_MINUTES = 30

    def __init__(
        self,
        meeting_repo: MeetingRepository,
    ):
        self.meeting_repo = meeting_repo

    def execute(self) -> CapacityMonitor:
        """Tính toán capacity hiện tại (sync version)"""
        now = get_current_utc7_time()
        window_end = now + timedelta(minutes=self.FORECAST_WINDOW_MINUTES)

        # MeetingRepository now has capacity methods directly
        n_current = self.meeting_repo.get_present_participants_count(now)
        n_incoming = self.meeting_repo.get_upcoming_participants_count(now, window_end)
        n_outgoing = self.meeting_repo.get_departing_participants_count(now, window_end)

        monitor = CapacityMonitor.calculate(
            n_current=n_current,
            n_incoming=n_incoming,
            n_outgoing=n_outgoing,
        )

        return monitor
