from datetime import datetime, timedelta
from typing import List, Optional

from app.meeting.domain.value_objects import ParticipantStatus
from app.shared.domain.base_entity import BaseEntity
from pydantic import BaseModel, ConfigDict, Field


class UserRef(BaseModel):
    """Tham chiếu đến User trong Domain (Value Object) — Pydantic để nhúng trong BaseEntity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    avatar_url: Optional[str] = None


class MeetingParticipant(BaseEntity):
    """Thành viên tham gia buổi họp (Domain Entity)"""

    user_id: int
    meeting_id: Optional[int] = None
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    status: ParticipantStatus = ParticipantStatus.NOT_JOINED
    link_image: Optional[str] = None
    user: Optional[UserRef] = None

    def check_in(self, check_in_time: datetime, image_url: str | None = None):
        """Thực hiện check-in cho thành viên (image_url tùy chọn, ví dụ quẹt thẻ)."""
        if self.status == ParticipantStatus.JOINED:
            return True, "Checkin thanh cong"

        self.check_in_at = check_in_time
        self.status = ParticipantStatus.JOINED
        self.link_image = image_url
        return True, "Checkin thanh cong"

    def check_out(self, check_out_time: datetime):
        """Thực hiện check-out cho thành viên."""
        if self.status == ParticipantStatus.COMPLETED:
            return True, "Da checkout"

        self.check_out_at = check_out_time
        self.status = ParticipantStatus.COMPLETED
        return True, "Checkout thanh cong"


class Meeting(BaseEntity):
    """Buổi họp (Domain Entity)"""

    title: str
    start_time: datetime
    end_time: datetime
    content: Optional[str] = None
    require_check_in: bool = True
    participants: List[MeetingParticipant] = Field(default_factory=list)

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
        return check_in_time > (self.start_time + timedelta(minutes=5))


MeetingParticipant.model_rebuild()
Meeting.model_rebuild()
