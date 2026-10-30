from abc import ABC, abstractmethod

from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import BasePermissionPayload
from app.permission_request.domain.value_objects import RequestCategory


class PermissionStrategy[TPayload: BasePermissionPayload](ABC):
    """
    Base Strategy Interface cho từng loại đơn xin phép.
    Mỗi Strategy phụ trách validation và side-effects riêng biệt.
    """

    @property
    @abstractmethod
    def category(self) -> RequestCategory:
        """Loại đơn mà Strategy này phục vụ."""
        ...

    @abstractmethod
    def validate(self, request: PermissionRequest[TPayload]) -> None:
        """Kiểm tra tính hợp lệ của đơn trước khi lưu trữ."""
        ...

    @abstractmethod
    async def on_created(
        self, request: PermissionRequest[TPayload], user_id: int
    ) -> None:
        """Thực thi các tác động trạng thái (side-effects) sau khi tạo đơn."""
        ...

    @abstractmethod
    def on_deleted(self, request: PermissionRequest[TPayload], user_id: int) -> None:
        """Khôi phục trạng thái (revert) khi đơn bị xóa hoặc hủy."""
        ...
