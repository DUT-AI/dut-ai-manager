from unittest.mock import AsyncMock, MagicMock
import pytest

from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.shared.infrastructure.notification_service import NotificationService


@pytest.mark.asyncio
async def test_notification_service_send_to_both_channels():
    # Setup mocks
    mock_discord = MagicMock()
    mock_discord.send_message_to_user = AsyncMock(return_value={"id": "msg_123"})

    mock_zalo = MagicMock()
    mock_zalo.send_message = AsyncMock(return_value={"msg_id": "zalo_123"})

    mock_user_repo = MagicMock()
    mock_user = MagicMock()
    mock_user.id = 10
    mock_user.name = "Nguyen Van A"
    mock_user.discord_id = "123456789"
    mock_user.zalo_bot_id = "zalo_987654"
    mock_user_repo.get_by_id.return_value = mock_user

    service = NotificationService(
        discord_service=mock_discord,
        zalo_bot=mock_zalo,
        user_repo=mock_user_repo,
    )

    payload = NotificationPayload(
        user_id=10,
        title="📚 BÀI TẬP MỚI",
        content="Nội dung bài tập test",
        category=NotificationCategory.HOMEWORK,
        level=NotificationLevel.INFO,
        image_asset="meme-hoc-bai.webp",
    )

    result = await service.send_to_user(payload)

    assert result == {"discord": True, "zalo": True}
    mock_discord.send_message_to_user.assert_awaited_once()
    mock_zalo.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_notification_service_fault_isolation():
    # When Discord throws exception, Zalo should still succeed
    mock_discord = MagicMock()
    mock_discord.send_message_to_user = AsyncMock(side_effect=Exception("Discord API error 500"))

    mock_zalo = MagicMock()
    mock_zalo.send_message = AsyncMock(return_value={"msg_id": "zalo_123"})

    mock_user_repo = MagicMock()
    mock_user = MagicMock()
    mock_user.id = 10
    mock_user.discord_id = "123456789"
    mock_user.zalo_bot_id = "zalo_987654"
    mock_user_repo.get_by_id.return_value = mock_user

    service = NotificationService(
        discord_service=mock_discord,
        zalo_bot=mock_zalo,
        user_repo=mock_user_repo,
    )

    payload = NotificationPayload(
        user_id=10,
        title="⚠️ CẢNH BÁO",
        content="Nội dung cảnh báo",
        category=NotificationCategory.VIOLATION,
        level=NotificationLevel.CRITICAL,
        image_asset="meme-doi-no-2.jpg",
    )

    result = await service.send_to_user(payload)

    assert result["discord"] is False
    assert result["zalo"] is True
