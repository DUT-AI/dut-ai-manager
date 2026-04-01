from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.meeting.domain.value_objects import ParticipantStatus


@dataclass
class UserRef:
    """Tham chiếu đến User trong Domain (Value Object)"""

    id: int
    name: str = ""
    avatar_url: Optional[str] = None


@dataclass
class MeetingParticipant:
    """Thành viên tham gia buổi họp (Domain Entity)"""

    user_id: int
    meeting_id: Optional[int] = None
    id: Optional[int] = None
    check_in_at: Optional[datetime] = None
    status: ParticipantStatus = ParticipantStatus.NOT_JOINED
    link_image: Optional[str] = None
    user: Optional[UserRef] = None

    def check_in(self, check_in_time: datetime, image_url: str):
        """Thực hiện check-in cho thành viên"""
        if self.status == ParticipantStatus.JOINED:
            return False, "Người dùng đã checkin rồi"

        self.check_in_at = check_in_time
        self.status = ParticipantStatus.JOINED
        self.link_image = image_url
        return True, "Checkin thành công"


@dataclass
class Meeting:
    """Buổi họp (Domain Entity)"""

    title: str
    start_time: datetime
    end_time: datetime
    id: Optional[int] = None
    content: Optional[str] = None
    require_check_in: bool = True
    participants: List[MeetingParticipant] = field(default_factory=list)

    def is_ongoing(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi họp có đang diễn ra hay không"""
        return self.start_time <= current_time <= self.end_time

    def is_finished(self, current_time: datetime) -> bool:
        """Kiểm tra xem buổi họp đã kết thúc chưa"""
        return current_time > self.end_time

    def is_late(self, check_in_time: datetime) -> bool:
        """Kiểm tra xem việc check-in có bị trễ hay không"""
        if not self.require_check_in:
            return False
        return check_in_time > self.start_time
