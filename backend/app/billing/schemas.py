from datetime import datetime
from typing import List, Optional

from app.billing.application.use_cases import QRGenerator
from app.billing.domain.entity import Invoice as DomainInvoice
from app.billing.domain.entity import InvoiceItemType, InvoiceStatus
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class InvoiceItemBase(BaseModel):
    item_type: InvoiceItemType
    reference_id: Optional[int] = None
    amount: int = 0
    note: Optional[str] = None


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InvoiceCreate(BaseModel):
    user_id: int
    items: List[InvoiceItemCreate]
    description: Optional[str] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount: int
    status: InvoiceStatus
    description: Optional[str]
    reference_code: str
    payment_method: str
    transaction_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItemResponse] = []
    
    # Virtual field
    qr_url: str = ""

    @classmethod
    def from_domain(cls, invoice: DomainInvoice) -> "InvoiceResponse":
        """Map domain Invoice to schema and generate QR URL."""
        # Ensure ID and timestamps exist
        if invoice.id is None:
            raise ValueError("Invoice must have an ID")
        
        # Build items
        items = [
            InvoiceItemResponse(
                id=item.id,  # type: ignore
                item_type=item.item_type,
                reference_id=item.reference_id,
                amount=item.amount,
                note=item.note
            ) for item in invoice.items
        ]
        
        response = cls(
            id=invoice.id,
            user_id=invoice.user_id,
            amount=invoice.amount,
            status=invoice.status,
            description=invoice.description,
            reference_code=invoice.reference_code,
            payment_method=invoice.payment_method,
            transaction_id=invoice.transaction_id,
            created_at=invoice.created_at or datetime.now(),
            updated_at=invoice.updated_at or datetime.now(),
            items=items,
            qr_url=QRGenerator.get_url(invoice)
        )
        return response


class SePayWebhookPayload(BaseModel):
    """
    SePay Webhook Payload structure.
    Based on SePay documentation.
    """
    id: int = Field(validation_alias=AliasChoices("id", "transaction_id"))
    gateway: str
    transactionDate: str = Field(validation_alias=AliasChoices("transaction_date", "transactionDate"))
    accountNumber: str = Field(validation_alias=AliasChoices("account_number", "accountNumber"))
    code: Optional[str] = None
    content: str  # This is the transfer description (where we find reference_code)
    transferType: str
    transferAmount: int = Field(validation_alias=AliasChoices("amount", "transferAmount"))
    accumulated: int = Field(default=0, validation_alias=AliasChoices("accumulator", "accumulated"))
    subAccount: Optional[str] = None
    referenceCode: Optional[str] = None  # Reference code in webhook might be an ID or string
    description: Optional[str] = None


class MonthlyInvoiceItemPreview(BaseModel):
    user_id: int
    user_name: str
    violation_count: int
    violation_amount: int
    fund_amount: int
    total_amount: int
    description: str


class MonthlyInvoicePreviewResponse(BaseModel):
    month: int
    year: int
    items: List[MonthlyInvoiceItemPreview]


class MonthlyInvoiceCreate(BaseModel):
    month: int
    year: int
    team_id: Optional[int] = None
    user_ids: List[int] = []
    violation_price: int = 20000
    fund_amount: int = 50000
    extra_items: List[InvoiceItemCreate] = []
    execute: bool = False  # If false, only return preview
