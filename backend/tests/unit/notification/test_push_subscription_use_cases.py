"""
Unit tests for Web Push Notification Use Cases.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.reminder.application.dtos import (
    PushSubscriptionKeysDto,
    PushSubscriptionRequestDto,
    UnregisterPushSubscriptionRequestDto,
)
from app.reminder.application.register_push_subscription_use_case import (
    RegisterPushSubscriptionUseCase,
)
from app.reminder.application.send_web_push_notification_use_case import (
    SendWebPushNotificationUseCase,
)
from app.reminder.application.unregister_push_subscription_use_case import (
    UnregisterPushSubscriptionUseCase,
)
from app.reminder.domain.entity import PushSubscription
from app.reminder.infrastructure.web_push_service import (
    DeadTokenException,
    WebPushService,
)


@pytest.fixture
def mock_push_repo():
    return MagicMock()


@pytest.fixture
def mock_web_push_service():
    return MagicMock(spec=WebPushService)


@pytest.fixture
def sample_subscription():
    return PushSubscription(
        id=1,
        user_id=10,
        endpoint="https://fcm.googleapis.com/fcm/send/sample_endpoint_1",
        p256dh="test_p256dh_key",
        auth="test_auth_secret",
        user_agent="Chrome on Android",
        is_active=True,
        created_at=datetime(2026, 10, 21, 10, 0, 0),
    )


def test_register_push_subscription_success(mock_push_repo, sample_subscription):
    mock_push_repo.save_or_update.return_value = sample_subscription

    use_case = RegisterPushSubscriptionUseCase(mock_push_repo)
    dto = PushSubscriptionRequestDto(
        endpoint="https://fcm.googleapis.com/fcm/send/sample_endpoint_1",
        keys=PushSubscriptionKeysDto(
            p256dh="test_p256dh_key",
            auth="test_auth_secret",
        ),
        user_agent="Chrome on Android",
    )

    result = use_case.execute(user_id=10, dto=dto)

    assert result.subscription_id == 1
    assert result.is_active is True
    mock_push_repo.save_or_update.assert_called_once_with(
        user_id=10,
        endpoint="https://fcm.googleapis.com/fcm/send/sample_endpoint_1",
        p256dh="test_p256dh_key",
        auth="test_auth_secret",
        user_agent="Chrome on Android",
    )


def test_unregister_push_subscription_success(mock_push_repo):
    mock_push_repo.deactivate_endpoint.return_value = True

    use_case = UnregisterPushSubscriptionUseCase(mock_push_repo)
    dto = UnregisterPushSubscriptionRequestDto(
        endpoint="https://fcm.googleapis.com/fcm/send/sample_endpoint_1",
    )

    result = use_case.execute(dto)

    assert result is True
    mock_push_repo.deactivate_endpoint.assert_called_once_with(
        "https://fcm.googleapis.com/fcm/send/sample_endpoint_1"
    )


def test_send_web_push_success(
    mock_push_repo, mock_web_push_service, sample_subscription
):
    mock_push_repo.get_active_by_user_id.return_value = [sample_subscription]
    mock_web_push_service.send_notification.return_value = True

    use_case = SendWebPushNotificationUseCase(mock_push_repo, mock_web_push_service)
    sent, failed = use_case.execute(
        user_id=10,
        title="Lịch họp Lab chiều nay",
        body="Họp lúc 14:00 tại phòng AI.",
        action_url="/dashboard/meetings/123",
    )

    assert sent == 1
    assert failed == 0
    mock_web_push_service.send_notification.assert_called_once()
    mock_push_repo.update_last_used.assert_called_once_with(1)


def test_send_web_push_dead_token_auto_deactivate(
    mock_push_repo, mock_web_push_service, sample_subscription
):
    mock_push_repo.get_active_by_user_id.return_value = [sample_subscription]
    mock_web_push_service.send_notification.side_effect = DeadTokenException(
        "Token 410 Gone"
    )

    use_case = SendWebPushNotificationUseCase(mock_push_repo, mock_web_push_service)
    sent, failed = use_case.execute(
        user_id=10,
        title="Nhắc nhở bài tập",
        body="Hạn chót hôm nay",
    )

    assert sent == 0
    assert failed == 1
    mock_push_repo.deactivate_endpoint.assert_called_once_with(
        sample_subscription.endpoint
    )


def test_send_web_push_no_subscriptions(mock_push_repo, mock_web_push_service):
    mock_push_repo.get_active_by_user_id.return_value = []

    use_case = SendWebPushNotificationUseCase(mock_push_repo, mock_web_push_service)
    sent, failed = use_case.execute(
        user_id=99,
        title="Thông báo",
        body="Nội dung",
    )

    assert sent == 0
    assert failed == 0
    mock_web_push_service.send_notification.assert_not_called()
