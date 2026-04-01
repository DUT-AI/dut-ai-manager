from dataclasses import dataclass
from datetime import date

from app.permission_request.domain.value_objects import RequestCategory


@dataclass
class PermissionRequestCreated:
    """Sự kiện yêu cầu mới được tạo"""

    request_id: int
    user_id: int
    category: RequestCategory
    date: date
    reason: str


@dataclass
class PermissionRequestUpdated:
    """Sự kiện yêu cầu được cập nhật"""

    request_id: int
