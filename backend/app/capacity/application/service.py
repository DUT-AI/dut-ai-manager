"""
Capacity Monitor Service

Service tính toán và lưu trạng thái cảnh báo quá tải.
"""

from datetime import datetime, timedelta
from typing import Optional
import json
from app.capacity.domain.entity import CapacityMonitor, CapacityStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.utils.datetime import get_current_utc7_time


class CapacityService:
    """Service quản lý capacity"""

    FORECAST_WINDOW_MINUTES = 30
    CACHE_KEY = "capacity:status"
    CACHE_TTL = 300  # 5 phút

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        redis_client=None,
    ):
        self.meeting_repo = meeting_repo
        self.redis = redis_client

    def calculate_current(self) -> CapacityMonitor:
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

    def get_current_status(self) -> CapacityMonitor:
        """Lấy trạng thái hiện tại"""
        return self.calculate_current()
