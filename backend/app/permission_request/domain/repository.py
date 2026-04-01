from typing import List, Optional, Protocol

from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.value_objects import RequestCategory


class PermissionRequestRepository(Protocol):
    """Port: lưu trữ PermissionRequest (triển khai ở infrastructure)."""

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[PermissionRequest]: ...

    def get_by_id(self, request_id: int) -> Optional[PermissionRequest]: ...

    def get_by_user(
        self,
        user_id: int,
        month: Optional[int] = None,
        year: Optional[int] = None,
        deleted: bool = False,
    ) -> List[PermissionRequest]: ...

    def get_by_month(
        self,
        month: int,
        year: int,
        limit: int = 1000,
        deleted: bool = False,
    ) -> List[PermissionRequest]: ...

    def count_by_user_category_month(
        self, user_id: int, category: RequestCategory, month: int, year: int
    ) -> int: ...

    def save(self, request: PermissionRequest) -> PermissionRequest: ...

    def delete(self, request_id: int) -> bool: ...

    def restore(self, request_id: int) -> bool: ...
