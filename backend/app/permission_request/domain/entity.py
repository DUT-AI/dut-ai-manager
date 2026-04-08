from datetime import datetime
from typing import Optional

from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.base_entity import BaseEntity

from app.user.domain.entity import UserEntity
from app.homework.domain.entity import Homework
from app.meeting.domain.entity import Meeting


class PermissionRequest(BaseEntity):
    """Yêu cầu xin phép (Domain Entity)"""

    user_id: Optional[int]
    category: RequestCategory
    note: str
    
    # Specific metadata based on category
    homework_id: Optional[int] = None
    meeting_id: Optional[int] = None
    
    # Target time (arrival time or deadline time)
    start_time: Optional[datetime] = None

    # Related entities (Optional)
    user: Optional[UserEntity] = None
    homework: Optional[Homework] = None
    meeting: Optional[Meeting] = None

    def is_absence(self) -> bool:
        return self.category == RequestCategory.ABSENCE

    def is_postpone(self) -> bool:
        return self.category == RequestCategory.POSTPONE


# Rebuild model for Pydantic to resolve type hints
PermissionRequest.model_rebuild()
