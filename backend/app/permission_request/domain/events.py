from datetime import datetime

from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.event_bus import DomainEvent


class PermissionRequestCreated(DomainEvent):
    """Sự kiện yêu cầu mới được tạo"""

    request_id: int
    user_id: int
    category: RequestCategory
    note: str
    start_time: datetime | None = None


class PermissionRequestUpdated(DomainEvent):
    """Sự kiện yêu cầu được cập nhật"""

    request_id: int


class MeetingParticipantTransferred(DomainEvent):
    """Sự kiện chuyển ca sinh hoạt thành công (đổi từ old_meeting_id sang new_meeting_id)"""

    request_id: int
    user_id: int
    old_meeting_id: int | None
    new_meeting_id: int
    note: str = ""

