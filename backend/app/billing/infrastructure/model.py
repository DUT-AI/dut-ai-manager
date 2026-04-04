"""
Billing ORM Models — SQLModel, infrastructure layer.
"""

from typing import TYPE_CHECKING, List, Optional

from app.billing.domain.entity import Invoice, InvoiceItem, InvoiceItemType, InvoiceStatus
from app.shared.infrastructure.base_model import TimestampMixin
from app.utils.datetime import get_current_utc7_time
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class InvoiceModel(TimestampMixin, table=True):
    """ORM model — maps to 'invoices' table."""

    __tablename__ = "invoices"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    amount: int = Field(default=0)
    status: str = Field(default=InvoiceStatus.PENDING, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    reference_code: str = Field(unique=True, index=True)
    payment_method: str = Field(default="sepay")
    transaction_id: Optional[str] = Field(default=None, unique=True, index=True)

    # Relationships
    items: List["InvoiceItemModel"] = Relationship(
        back_populates="invoice",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    user_rel: Optional["UserModel"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[InvoiceModel.user_id]"}
    )

    def to_entity(self) -> Invoice:
        """ORM Model → Domain Entity."""
        return Invoice(
            id=self.id,
            user_id=self.user_id,
            amount=self.amount,
            status=InvoiceStatus(self.status),
            description=self.description,
            reference_code=self.reference_code,
            payment_method=self.payment_method,
            transaction_id=self.transaction_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
            items=[item.to_entity() for item in self.items],
        )

    @classmethod
    def from_entity(cls, entity: Invoice) -> "InvoiceModel":  # type: ignore
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            amount=entity.amount,
            status=entity.status,
            description=entity.description,
            reference_code=entity.reference_code,
            payment_method=entity.payment_method,
            transaction_id=entity.transaction_id,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_deleted=entity.is_deleted,
        )


class InvoiceItemModel(TimestampMixin, table=True):
    """ORM model — maps to 'invoice_items' table."""

    __tablename__ = "invoice_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoices.id", index=True)
    item_type: str = Field()
    reference_id: Optional[int] = Field(default=None)
    amount: int = Field(default=0)
    note: Optional[str] = Field(default=None, max_length=500)

    # Relationships
    invoice: Optional[InvoiceModel] = Relationship(back_populates="items")

    def to_entity(self) -> InvoiceItem:
        """ORM Model → Domain Entity."""
        return InvoiceItem(
            id=self.id,
            invoice_id=self.invoice_id,
            item_type=InvoiceItemType(self.item_type),
            reference_id=self.reference_id,
            amount=self.amount,
            note=self.note,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: InvoiceItem) -> "InvoiceItemModel":  # type: ignore
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            invoice_id=entity.invoice_id,  # type: ignore
            item_type=entity.item_type,
            reference_id=entity.reference_id,
            amount=entity.amount,
            note=entity.note,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_deleted=entity.is_deleted,
        )
