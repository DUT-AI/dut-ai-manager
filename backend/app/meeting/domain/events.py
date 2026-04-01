from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class MeetingCreated:
    """Sự kiện buổi họp mới được tạo"""

    meeting_id: int
    title: str
    user_ids: List[int]
    start_time: str
    end_time: str


@dataclass
class MeetingUpdated:
    """Sự kiện buổi họp được cập nhật"""

    meeting_id: int
    title: str
    user_ids: List[int]
    start_time: str
    end_time: str


@dataclass
class ParticipantCheckedIn:
    """Sự kiện thành viên điểm danh"""

    meeting_id: int
    user_id: int
    check_in_at: datetime
    is_late: bool
    meeting_title: str
