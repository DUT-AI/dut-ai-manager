"""
Billing Domain Entities — pure Pydantic, NO ORM dependency.
"""

from enum import Enum
from typing import List, Optional

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

    invoice_id: Optional[int] = None
    item_type: InvoiceItemType
    reference_id: Optional[int] = None  # Original ID (e.g., violation_id)
    amount: int = 0
    note: Optional[str] = ""


class Invoice(BaseEntity):
    """Domain entity representing a billing invoice."""

    user_id: int
    amount: int = 0
    status: InvoiceStatus = InvoiceStatus.PENDING
    description: Optional[str] = ""
    reference_code: str  # Unique code for payment (e.g., DUTINV12345)
    payment_method: str = "sepay"
    transaction_id: Optional[str] = None  # From SePay after payment

    # Relationship items
    items: List[InvoiceItem] = []

