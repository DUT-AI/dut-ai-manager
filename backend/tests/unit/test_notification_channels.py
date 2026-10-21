"""
Unit tests for Notification Channel Adapters (InApp, Discord, Zalo, WebPush).
Verifies retry backoff, formatting, and edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.infrastructure.notification.channel import ChannelType
from app.shared.infrastructure.notification.discord_channel import (
    DiscordNotificationChannel,
)
from app.shared.infrastructure.notification.in_app_channel import (
    InAppNotificationChannel,
)
from app.shared.infrastructure.notification.web_push_channel import (
    WebPushNotificationChannel,
)
from app.shared.infrastructure.notification.zalo_channel import ZaloNotificationChannel
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.user.domain.entity import UserEntity as User


@pytest.fixture
def sample_user():
    return User(
        id=1,
        email="student@dut.udn.vn",
        name="Lê Văn B",
        discord_id="987654321",
        zalo_bot_id="zalo_987",
    )


@pytest.fixture
def sample_payload():
    return NotificationPayload(
        user_id=1,
        title="Thông Báo Kiểm Tra",
        content="Nội dung kiểm tra hệ thống",
        category=NotificationCategory.HOMEWORK,
        level=NotificationLevel.INFO,
        action_url="/homework/1",
    )


# ================= InAppNotificationChannel Tests =================


@pytest.mark.asyncio
async def test_in_app_channel_success(sample_user, sample_payload):
    mock_repo = MagicMock()
    mock_repo.add.return_value = MagicMock()

    channel = InAppNotificationChannel(notification_repo=mock_repo)
    result = await channel.send(sample_user, sample_payload)

    assert result.channel == ChannelType.IN_APP
    assert result.success is True
    assert result.status == "SAVED"
    mock_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_in_app_channel_error(sample_user, sample_payload):
    mock_repo = MagicMock()
    mock_repo.add.side_effect = Exception("DB Connection Lost")

    channel = InAppNotificationChannel(notification_repo=mock_repo)
    result = await channel.send(sample_user, sample_payload)

    assert result.success is False
    assert result.status == "FAILED"
    assert "DB Connection Lost" in result.error_message


# ================= DiscordNotificationChannel Tests =================


@pytest.mark.asyncio
async def test_discord_channel_no_discord_id(sample_payload):
    user_without_discord = User(
        id=2, email="u2@dut.udn.vn", name="User 2", discord_id=None
    )
    mock_discord_service = MagicMock()

    channel = DiscordNotificationChannel(discord_service=mock_discord_service)
    result = await channel.send(user_without_discord, sample_payload)

    assert result.success is False
    assert result.status == "NO_DISCORD_ID"
    mock_discord_service.send_message_to_user.assert_not_called()


@pytest.mark.asyncio
async def test_discord_channel_dm_blocked(sample_user, sample_payload):
    mock_discord_service = MagicMock()
    mock_discord_service.send_message_to_user = AsyncMock(
        side_effect=Exception("50007: Cannot send messages to this user")
    )

    channel = DiscordNotificationChannel(discord_service=mock_discord_service)
    result = await channel.send(sample_user, sample_payload)

    assert result.success is False
    assert result.status == "DM_BLOCKED"
    # Khi gặp lỗi DM blocked, dừng ngay không retry vô ích
    assert mock_discord_service.send_message_to_user.call_count == 1


@pytest.mark.asyncio
async def test_discord_channel_retry_success(sample_user, sample_payload):
    mock_discord_service = MagicMock()
    # Lần 1 fail tạm thời, lần 2 thành công
    mock_discord_service.send_message_to_user = AsyncMock(
        side_effect=[Exception("Rate limit 429"), True]
    )

    channel = DiscordNotificationChannel(discord_service=mock_discord_service)
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await channel.send(sample_user, sample_payload)

    assert result.success is True
    assert result.status == "SENT"
    assert mock_discord_service.send_message_to_user.call_count == 2


# ================= ZaloNotificationChannel Tests =================


@pytest.mark.asyncio
async def test_zalo_channel_no_zalo_id(sample_payload):
    user_without_zalo = User(
        id=3, email="u3@dut.udn.vn", name="User 3", zalo_bot_id=None
    )
    mock_zalo_bot = MagicMock()

    channel = ZaloNotificationChannel(zalo_bot=mock_zalo_bot)
    result = await channel.send(user_without_zalo, sample_payload)

    assert result.success is False
    assert result.status == "NO_ZALO_ID"
    mock_zalo_bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_zalo_channel_retry_success(sample_user, sample_payload):
    mock_zalo_bot = MagicMock()
    mock_zalo_bot.send_message = AsyncMock(
        side_effect=[Exception("Network Timeout"), {"message_id": "zalo_msg_1"}]
    )

    channel = ZaloNotificationChannel(zalo_bot=mock_zalo_bot)
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await channel.send(sample_user, sample_payload)

    assert result.success is True
    assert result.status == "SENT"
    assert mock_zalo_bot.send_message.call_count == 2


# ================= WebPushNotificationChannel Tests =================


@pytest.mark.asyncio
async def test_web_push_channel_success(sample_user, sample_payload):
    mock_uc = MagicMock()
    mock_uc.execute.return_value = (1, 0)  # (sent=1, failed=0)

    channel = WebPushNotificationChannel(send_web_push_use_case=mock_uc)
    result = await channel.send(sample_user, sample_payload)

    assert result.success is True
    assert result.status == "SENT"


@pytest.mark.asyncio
async def test_web_push_channel_no_subscriptions(sample_user, sample_payload):
    mock_uc = MagicMock()
    mock_uc.execute.return_value = (0, 0)  # (sent=0, failed=0)

    channel = WebPushNotificationChannel(send_web_push_use_case=mock_uc)
    result = await channel.send(sample_user, sample_payload)

    assert result.success is False
    assert result.status == "NO_SUBSCRIPTION"
