from datetime import datetime

from app.homework.domain.entity import Homework
from app.meeting.domain.entity import Meeting
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import UserRef


class PermissionRequest(BaseEntity):
    """Yêu cầu xin phép (Domain Entity)"""

    user_id: int | None
    category: RequestCategory
    note: str

    # Specific metadata based on category
    homework_id: int | None = None
    meeting_id: int | None = None

    # Target time (arrival time or deadline time)
    start_time: datetime | None = None

    # Related entities (Optional)
    owner: UserRef | None = None
    creator: UserRef | None = None
    updater: UserRef | None = None
    homework: Homework | None = None
    meeting: Meeting | None = None

    def validate_postpone(self, homework: Homework) -> None:
        """Kiểm tra tính hợp lệ của đơn xin hoãn bài tập (tối đa 4 ngày)."""
        if self.category != RequestCategory.POSTPONE:
            return

        if self.start_time:
            delta = self.start_time - homework.deadline
            if delta.total_seconds() > 4 * 24 * 3600:
                raise ValueError(
                    "Thời gian xin hoãn không được vượt quá 4 ngày so với deadline gốc"
                )
            if delta.total_seconds() < 0:
                raise ValueError("Thời gian gia hạn mới phải sau deadline gốc")


# Rebuild model for Pydantic to resolve type hints
PermissionRequest.model_rebuild()
