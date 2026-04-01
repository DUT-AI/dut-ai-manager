from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from app.permission_request.domain.value_objects import RequestCategory


@dataclass
class PermissionRequest:
    """Yêu cầu xin phép (Domain Entity)"""

    user_id: int
    category: RequestCategory
    date: date
    reason: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_absence(self) -> bool:
        return self.category == RequestCategory.ABSENCE

    def is_postpone(self) -> bool:
        return self.category == RequestCategory.POSTPONE
