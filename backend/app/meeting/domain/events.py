from datetime import datetime
from typing import List
from app.shared.domain.event_bus import DomainEvent


class MeetingCreated(DomainEvent):
    """Sự kiện buổi họp mới được tạo"""

    meeting_id: int
    title: str
    user_ids: List[int]
    start_time: str
    end_time: str


class MeetingUpdated(DomainEvent):
    """Sự kiện buổi họp được cập nhật"""

    meeting_id: int
    title: str
    user_ids: List[int]
    start_time: str
    end_time: str


class ParticipantCheckedIn(DomainEvent):
    """Sự kiện thành viên điểm danh"""

    meeting_id: int
    user_id: int
    check_in_at: datetime
    is_late: bool
    meeting_title: str


class ParticipantCheckedOut(DomainEvent):
    """Sự kiện thành viên rời đi (checkout)"""

    meeting_id: int
    user_id: int
    check_out_at: datetime
    meeting_title: str


class MeetingAbsenceDetected(DomainEvent):
    """Sự kiện phát hiện vắng mặt không phép"""

    user_id: int
    meeting_id: int
    meeting_title: str
    meeting_date: str
