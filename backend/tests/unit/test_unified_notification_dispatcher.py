"""
Unit tests for UnifiedNotificationDispatcher.
Tests In-App DB persistence, fault isolation across channels, and parallel dispatching.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    ChannelType,
)
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.user.domain.entity import UserEntity as User


@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    user = User(
        id=1,
        email="test@dut.udn.vn",
        name="Nguyễn Văn A",
        discord_id="123456789",
        zalo_bot_id="zalo_123",
    )
    repo.get_by_id.return_value = user
    return repo


@pytest.fixture
def mock_in_app_channel():
    channel = MagicMock()
    channel.channel_type = ChannelType.IN_APP
    channel.send = AsyncMock(
        return_value=ChannelDeliveryResult(
            channel=ChannelType.IN_APP, success=True, status="SAVED"
        )
    )
    return channel


@pytest.fixture
def mock_discord_channel():
    channel = MagicMock()
    channel.channel_type = ChannelType.DISCORD
    channel.send = AsyncMock(
        return_value=ChannelDeliveryResult(
            channel=ChannelType.DISCORD, success=True, status="SENT"
        )
    )
    channel.send_room = AsyncMock(
        return_value=ChannelDeliveryResult(
            channel=ChannelType.DISCORD, success=True, status="SENT"
        )
    )
    return channel


@pytest.fixture
def mock_zalo_channel():
    channel = MagicMock()
    channel.channel_type = ChannelType.ZALO
    channel.send = AsyncMock(
        return_value=ChannelDeliveryResult(
            channel=ChannelType.ZALO, success=True, status="SENT"
        )
    )
    return channel


@pytest.fixture
def mock_web_push_channel():
    channel = MagicMock()
    channel.channel_type = ChannelType.WEB_PUSH
    channel.send = AsyncMock(
        return_value=ChannelDeliveryResult(
            channel=ChannelType.WEB_PUSH, success=True, status="SENT"
        )
    )
    return channel


@pytest.fixture
def dispatcher(
    mock_user_repo,
    mock_in_app_channel,
    mock_discord_channel,
    mock_zalo_channel,
    mock_web_push_channel,
):
    return UnifiedNotificationDispatcher(
        user_repo=mock_user_repo,
        in_app_channel=mock_in_app_channel,
        discord_channel=mock_discord_channel,
        zalo_channel=mock_zalo_channel,
        web_push_channel=mock_web_push_channel,
    )


@pytest.mark.asyncio
async def test_dispatch_saves_in_app_notification_first(
    dispatcher, mock_in_app_channel, mock_user_repo
):
    """Xác nhận luôn lưu In-App DB trước tiên khi dispatch thông báo."""
    payload = NotificationPayload(
        user_id=1,
        title="Test Title",
        content="Test Content",
        category=NotificationCategory.HOMEWORK,
        level=NotificationLevel.INFO,
    )

    res = await dispatcher.dispatch(payload)

    assert res["in_app"] is True
    assert res["queued"] is True
    mock_in_app_channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatch_now_calls_all_channels(
    dispatcher,
    mock_in_app_channel,
    mock_discord_channel,
    mock_zalo_channel,
    mock_web_push_channel,
):
    """Xác nhận dispatch_now gọi đầy đủ tất cả các kênh (In-App, Discord, Zalo, Web Push)."""
    payload = NotificationPayload(
        user_id=1,
        title="Meeting Title",
        content="Meeting Content",
        category=NotificationCategory.MEETING,
        level=NotificationLevel.SUCCESS,
    )

    results = await dispatcher.dispatch_now(payload)

    assert "in_app" in results
    assert "discord" in results
    assert "zalo" in results
    assert "web_push" in results

    assert results["in_app"].success is True
    assert results["discord"].success is True
    assert results["zalo"].success is True
    assert results["web_push"].success is True


@pytest.mark.asyncio
async def test_dispatch_fault_isolation(
    dispatcher,
    mock_in_app_channel,
    mock_discord_channel,
    mock_zalo_channel,
    mock_web_push_channel,
):
    """Xác nhận khi một kênh bên ngoài (Discord) ném Exception, các kênh khác vẫn hoạt động bình thường."""
    mock_discord_channel.send = AsyncMock(
        side_effect=Exception("Discord API 500 Server Error")
    )

    payload = NotificationPayload(
        user_id=1,
        title="Billing Title",
        content="Billing Content",
        category=NotificationCategory.BILLING,
        level=NotificationLevel.WARNING,
    )

    # Không được ném ngoại lệ ra ngoài
    results = await dispatcher.dispatch_now(payload)

    assert results["in_app"].success is True
    assert results["discord"].success is False
    assert results["discord"].status == "FAILED"
    assert "Discord API 500" in results["discord"].error_message

    # Zalo và Web Push vẫn gửi thành công
    assert results["zalo"].success is True
    assert results["web_push"].success is True


@pytest.mark.asyncio
async def test_dispatch_user_not_found(dispatcher, mock_user_repo, mock_in_app_channel):
    """Khi user không tồn tại, dispatcher không gửi tin và bỏ qua."""
    mock_user_repo.get_by_id.return_value = None

    payload = NotificationPayload(
        user_id=9999,
        title="Not Found",
        content="Content",
        category=NotificationCategory.SYSTEM,
    )

    res = await dispatcher.dispatch(payload)
    assert res == {"in_app": False, "queued": False}
    mock_in_app_channel.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_dispatch_room(dispatcher, mock_discord_channel):
    """Xác nhận dispatch_room chuyển tiếp yêu cầu đến Discord channel."""
    payload = NotificationPayload(
        user_id=1,
        title="Admin Report",
        content="New report submitted",
        category=NotificationCategory.PERMISSION_REQUEST,
    )

    res = await dispatcher.dispatch_room("123456_room", payload)
    assert res.success is True
    mock_discord_channel.send_room.assert_awaited_once_with("123456_room", payload)
