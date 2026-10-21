"""
RegisterPushSubscriptionUseCase — Single-Responsibility Use Case.
Lưu hoặc tái kích hoạt thông tin thiết bị nhận Web Push của người dùng.
"""

from app.reminder.application.dtos import (
    PushSubscriptionRequestDto,
    PushSubscriptionResponseDto,
)
from app.reminder.domain.repository import PushSubscriptionRepository


class RegisterPushSubscriptionUseCase:
    """Use Case đăng ký thiết bị nhận thông báo đẩy."""

    def __init__(self, repo: PushSubscriptionRepository):
        self.repo = repo

    def execute(
        self,
        user_id: int,
        dto: PushSubscriptionRequestDto,
    ) -> PushSubscriptionResponseDto:
        subscription = self.repo.save_or_update(
            user_id=user_id,
            endpoint=dto.endpoint,
            p256dh=dto.keys.p256dh,
            auth=dto.keys.auth,
            user_agent=dto.user_agent,
        )
        return PushSubscriptionResponseDto(
            subscription_id=subscription.id or 0,
            is_active=subscription.is_active,
        )
