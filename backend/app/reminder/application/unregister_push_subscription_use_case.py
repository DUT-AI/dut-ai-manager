"""
UnregisterPushSubscriptionUseCase — Single-Responsibility Use Case.
Hủy kích hoạt kênh thông báo đẩy của thiết bị hiện tại khi người dùng đăng xuất.
"""

from app.reminder.application.dtos import UnregisterPushSubscriptionRequestDto
from app.reminder.domain.repository import PushSubscriptionRepository


class UnregisterPushSubscriptionUseCase:
    """Use Case hủy đăng ký thiết bị nhận thông báo đẩy."""

    def __init__(self, repo: PushSubscriptionRepository):
        self.repo = repo

    def execute(self, dto: UnregisterPushSubscriptionRequestDto) -> bool:
        return self.repo.deactivate_endpoint(dto.endpoint)
