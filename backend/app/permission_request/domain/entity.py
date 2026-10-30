from datetime import datetime

from app.permission_request.domain.payloads import (
    AbsencePayload,
    BasePermissionPayload,
    ChangeMeetingPayload,
    LatePayload,
    PermissionPayloadUnion,
    PostponePayload,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import UserRef


class PermissionRequest[TPayload: BasePermissionPayload](BaseEntity):
    """
    Yêu cầu xin phép (Generic Domain Entity).
    TPayload: Kiểu dữ liệu đặc thù của loại đơn (AbsencePayload, LatePayload,...),
              đảm bảo 100% Type-Safe và không dùng Any hay getattr.
    """

    user_id: int | None
    note: str
    payload: TPayload

    # Related entities (Optional snapshots)
    creator: UserRef | None = None
    updater: UserRef | None = None

    @property
    def category(self) -> RequestCategory:
        """Loại yêu cầu xin phép (truy xuất từ payload)."""
        return self.payload.category

    @property
    def homework_id(self) -> int | None:
        """ID bài tập liên kết nếu là đơn hoãn bài tập."""
        match self.payload:
            case PostponePayload(homework_id=hid):
                return hid
            case _:
                return None

    @property
    def meeting_id(self) -> int | None:
        """ID buổi học liên kết nếu là đơn vắng, trễ, hoặc đổi ca."""
        match self.payload:
            case (
                AbsencePayload(meeting_id=mid)
                | LatePayload(meeting_id=mid)
                | ChangeMeetingPayload(meeting_id=mid)
            ):
                return mid
            case _:
                return None

    @property
    def old_meeting_id(self) -> int | None:
        """ID buổi học cũ nếu là đơn đổi ca."""
        match self.payload:
            case ChangeMeetingPayload(old_meeting_id=old_mid):
                return old_mid
            case _:
                return None

    @property
    def start_time(self) -> datetime | None:
        """Thời gian bắt đầu/hạn nộp liên kết với đơn."""
        match self.payload:
            case (
                LatePayload(start_time=st)
                | PostponePayload(start_time=st)
                | ChangeMeetingPayload(start_time=st)
            ):
                return st
            case _:
                return None


# Type alias cho PermissionRequest khi làm việc với Union payload
PermissionRequestUnion = PermissionRequest[PermissionPayloadUnion]
