from datetime import date, datetime

from app.shared.domain.event_bus import DomainEvent


class InvoiceCreated(DomainEvent):
    """Sự kiện phát ra khi một hóa đơn mới được tạo."""

    invoice_id: int
    user_id: int
    amount: int
    reference_code: str
    description: str | None = None
    billing_period: date
    occurred_at: datetime | None = None


class InvoicePaid(DomainEvent):
    """Sự kiện phát ra khi một hóa đơn được thanh toán thành công."""

    invoice_id: int
    user_id: int
    amount: int
    reference_code: str
    transaction_id: str
    paid_at: datetime
    occurred_at: datetime | None = None
