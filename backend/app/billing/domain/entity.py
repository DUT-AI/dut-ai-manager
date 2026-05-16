"""
Billing Domain Entities — pure Pydantic, NO ORM dependency.
"""

from enum import Enum

from app.shared.domain.base_entity import BaseEntity


class InvoiceStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class InvoiceItemType(str, Enum):
    VIOLATION = "VIOLATION"
    FUND = "FUND"
    DINING = "DINING"
    OTHER = "OTHER"


class InvoiceItem(BaseEntity):
    """Domain entity representing an item in an invoice."""

    invoice_id: int | None = None
    item_type: InvoiceItemType
    reference_id: int | None = None  # Original ID (e.g., violation_id)
    amount: int = 0
    note: str | None = ""


class Invoice(BaseEntity):
    """Domain entity representing a billing invoice."""

    user_id: int
    amount: int = 0
    status: InvoiceStatus = InvoiceStatus.PENDING
    description: str | None = ""
    reference_code: str  # Unique code for payment (e.g., DUTINV12345)
    payment_method: str = "sepay"
    transaction_id: str | None = None  # From SePay after payment

    # Relationship items
    items: list[InvoiceItem] = []
