from datetime import datetime, timedelta

from pydantic import Field

from app.meeting.domain.participant import MeetingParticipant
from app.meeting.domain.value_objects import UserRef
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.datetime_types import ensure_utc


class Meeting(BaseEntity):
    """Buổi họp / Lớp học (Domain Entity - Write Aggregate)"""

    title: str
    start_time: datetime
    end_time: datetime
    content: str | None = None
    require_check_in: bool = True
    enable_evaluation: bool = False
    participants: list[MeetingParticipant] = Field(default_factory=list)
    creator: UserRef | None = None

    @property
    def evaluation_deadline(self) -> datetime | None:
        """Hạn chót đánh giá: Single Source of Truth tính động từ end_time + 24h."""
        if not self.enable_evaluation:
            return None
        return self.end_time + timedelta(hours=24)

    def is_evaluation_open(self, current_time: datetime) -> tuple[bool, str]:
        """Kiểm tra điều kiện mở cổng đánh giá 2 chiều (Domain Business Rule)."""
        if not self.enable_evaluation:
            return False, "Buổi học không kích hoạt tính năng đánh giá 2 chiều."
        if ensure_utc(current_time) < ensure_utc(self.start_time):
            return False, "Buổi học chưa bắt đầu, chưa thể gửi đánh giá."
        return True, "Cổng đánh giá đang mở."

    def is_evaluation_expired(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi học đã quá hạn 24h để đánh giá hay chưa."""
        if not self.enable_evaluation:
            return False
        deadline = self.evaluation_deadline
        return deadline is not None and ensure_utc(current_time) > ensure_utc(deadline)

    def is_ongoing(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi họp có đang diễn ra hay không"""
        cur = ensure_utc(current_time)
        return ensure_utc(self.start_time) <= cur <= ensure_utc(self.end_time)

    def is_finished(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi họp đã kết thúc chưa"""
        return ensure_utc(current_time) > ensure_utc(self.end_time)

    def is_late(self, check_in_time: datetime) -> bool:
        """Kiểm tra xem việc check-in có bị trễ hay không"""
        if not self.require_check_in:
            return False
        ci = ensure_utc(check_in_time)
        st = ensure_utc(self.start_time)
        return ci > (st + timedelta(minutes=5))

    def calculate_available_seats(
        self,
        max_seats: int,
        absence_user_ids: set[int] | None = None,
    ) -> int:
        """
        Tính số ghế khả dụng còn lại của buổi họp:
        Ghế khả dụng = MAX_SEATS - (Số participant active không có đơn ABSENCE hợp lệ)
        """
        valid_absence_ids = absence_user_ids or set()
        active_participants = [
            p
            for p in self.participants
            if not p.is_deleted and p.user_id not in valid_absence_ids
        ]
        occupied_count = len(active_participants)
        return max(0, max_seats - occupied_count)


Meeting.model_rebuild()

__all__ = ["Meeting"]
