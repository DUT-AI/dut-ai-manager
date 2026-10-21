"""
Abstract Repository Interface for PushSubscription domain.
Pure Python abstract class with zero framework dependencies.
"""

from abc import ABC, abstractmethod

from app.reminder.domain.entity import PushSubscription


class PushSubscriptionRepository(ABC):
    """Giao diện Repository cho PushSubscription."""

    @abstractmethod
    def save_or_update(
        self,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None = None,
    ) -> PushSubscription:
        """Lưu hoặc cập nhật token đăng ký Web Push."""
        pass

    @abstractmethod
    def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        """Tìm đăng ký theo endpoint."""
        pass

    @abstractmethod
    def get_active_by_user_id(self, user_id: int) -> list[PushSubscription]:
        """Lấy danh sách các đăng ký đang hoạt động của user."""
        pass

    @abstractmethod
    def deactivate_endpoint(self, endpoint: str) -> bool:
        """Đánh dấu vô hiệu hóa endpoint (is_active = False)."""
        pass

    @abstractmethod
    def update_last_used(self, subscription_id: int) -> None:
        """Cập nhật mốc thời gian vừa gửi thành công."""
        pass

    @abstractmethod
    def delete_endpoint(self, endpoint: str) -> bool:
        """Xóa hẳn endpoint khỏi hệ thống."""
        pass
