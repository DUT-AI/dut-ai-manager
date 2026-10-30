import asyncio

from loguru import logger

from app.billing.domain.events import InvoiceCreated, InvoicePaid
from app.core.config import settings
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)


class BillingNotificationHandler(EventHandler):
    """Xử lý gửi thông báo đa kênh (In-App DB, Discord, Zalo, Web Push) cho các sự kiện của Billing."""

    def __init__(
        self,
        dispatcher: UnifiedNotificationDispatcher,
    ):
        self.dispatcher = dispatcher

    async def handle(self, event: InvoiceCreated | InvoicePaid) -> None:
        """EntryPoint cho EventBus điều hướng sự kiện hóa đơn."""
        try:
            if isinstance(event, InvoiceCreated):
                asyncio.create_task(self._send_invoice_created_task(event))
            elif isinstance(event, InvoicePaid):
                asyncio.create_task(self._send_invoice_paid_task(event))
        except Exception as e:
            logger.error(f"Error in BillingNotificationHandler.handle: {e}")

    async def _send_invoice_created_task(self, event: InvoiceCreated) -> None:
        """Gửi thông báo hóa đơn mới cần thanh toán kèm meme xin tiền."""
        try:
            formatted_amount = f"{event.amount:,} VNĐ"
            period_str = event.billing_period.strftime("%m/%Y")

            frontend_url = settings.FRONTEND_URL
            action_url = f"{frontend_url.rstrip('/')}/dashboard/invoices"

            payload = NotificationPayload(
                user_id=event.user_id,
                title="💰 HÓA ĐƠN MỚI CẦN THANH TOÁN",
                content=(
                    f"Bạn có 01 hóa đơn mới kỳ tháng {period_str} cần thanh toán.\n"
                    f"Mô tả: {event.description or 'Các khoản thu định kỳ/vi phạm'}"
                ),
                category=NotificationCategory.BILLING,
                level=NotificationLevel.WARNING,
                image_asset="meme-xin-tien.jpeg",
                fields=[
                    {"name": "Số tiền", "value": formatted_amount, "inline": True},
                    {
                        "name": "Mã thanh toán",
                        "value": str(event.reference_code),
                        "inline": True,
                    },
                    {
                        "name": "Nội dung chuyển khoản",
                        "value": f"Chuyển chính xác nội dung: {event.reference_code}",
                        "inline": False,
                    },
                ],
                action_url=action_url,
                metadata={
                    "invoice_id": event.invoice_id,
                    "amount": event.amount,
                    "code": event.reference_code,
                },
            )

            await self.dispatcher.dispatch(payload)
        except Exception as e:
            logger.error(f"Error in _send_invoice_created_task: {e}")

    async def _send_invoice_paid_task(self, event: InvoicePaid) -> None:
        """Gửi thông báo xác nhận thanh toán thành công kèm meme chúc mừng."""
        try:
            formatted_amount = f"{event.amount:,} VNĐ"

            frontend_url = settings.FRONTEND_HOST
            action_url = (
                f"{frontend_url.rstrip('/')}/dashboard/invoices"
                if frontend_url
                else "/dashboard/invoices"
            )

            payload = NotificationPayload(
                user_id=event.user_id,
                title="✅ THANH TOÁN THÀNH CÔNG",
                content=(
                    f"Hệ thống đã nhận được khoản thanh toán {formatted_amount} của bạn.\n"
                    f"Cảm ơn bạn đã hoàn thành nghĩa vụ tài chính đúng hạn!"
                ),
                category=NotificationCategory.BILLING,
                level=NotificationLevel.SUCCESS,
                image_asset="meme-lam-viec-3.jpeg",
                fields=[
                    {
                        "name": "Số tiền đã nộp",
                        "value": formatted_amount,
                        "inline": True,
                    },
                    {
                        "name": "Mã hóa đơn",
                        "value": str(event.reference_code),
                        "inline": True,
                    },
                    {
                        "name": "Mã giao dịch",
                        "value": str(event.transaction_id),
                        "inline": False,
                    },
                ],
                action_url=action_url,
                metadata={
                    "invoice_id": event.invoice_id,
                    "amount": event.amount,
                    "code": event.reference_code,
                },
            )

            await self.dispatcher.dispatch(payload)
        except Exception as e:
            logger.error(f"Error in _send_invoice_paid_task: {e}")
