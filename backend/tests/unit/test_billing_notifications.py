from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.billing.application.notification_handler import BillingNotificationHandler
from app.billing.domain.events import InvoiceCreated, InvoicePaid
from app.shared.infrastructure.notification_payload import NotificationCategory


@pytest.mark.asyncio
async def test_billing_notification_handler_invoice_created():
    mock_notification_service = MagicMock()
    mock_notification_service.send_to_user = AsyncMock(
        return_value={"discord": True, "zalo": True}
    )

    handler = BillingNotificationHandler(notification_service=mock_notification_service)

    event = InvoiceCreated(
        invoice_id=1,
        user_id=10,
        amount=50000,
        reference_code="DUT123456",
        description="Tiền quỹ tháng 10",
        billing_period=date(2026, 10, 1),
    )

    await handler._send_invoice_created_task(event)

    mock_notification_service.send_to_user.assert_awaited_once()
    payload = mock_notification_service.send_to_user.call_args[0][0]

    assert payload.user_id == 10
    assert payload.category == NotificationCategory.BILLING
    assert payload.image_asset == "meme-xin-tien.jpeg"
    assert "50,000 VNĐ" in payload.fields[0]["value"]
    assert "DUT123456" in payload.fields[1]["value"]


@pytest.mark.asyncio
async def test_billing_notification_handler_invoice_paid():
    mock_notification_service = MagicMock()
    mock_notification_service.send_to_user = AsyncMock(
        return_value={"discord": True, "zalo": True}
    )

    handler = BillingNotificationHandler(notification_service=mock_notification_service)

    event = InvoicePaid(
        invoice_id=1,
        user_id=10,
        amount=50000,
        reference_code="DUT123456",
        transaction_id="TX_999888",
        paid_at=datetime.now(UTC),
    )

    await handler._send_invoice_paid_task(event)

    mock_notification_service.send_to_user.assert_awaited_once()
    payload = mock_notification_service.send_to_user.call_args[0][0]

    assert payload.user_id == 10
    assert payload.category == NotificationCategory.BILLING
    assert payload.image_asset == "meme-lam-viec-3.jpeg"
    assert "TX_999888" in payload.fields[2]["value"]
