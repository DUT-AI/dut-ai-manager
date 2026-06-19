"""
Billing ORM Models — SQLAlchemy 2.0, infrastructure layer.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.billing.domain.entity import (
    Invoice,
    InvoiceItem,
    InvoiceItemType,
    InvoiceStatus,
)
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.utils.datetime import get_current_utc7_time

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class InvoiceModel(SQLAlchemyTimestampMixin, Base):
    """ORM model — maps to 'invoices' table."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(50), default=InvoiceStatus.PENDING, index=True
    )
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    reference_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    payment_method: Mapped[str] = mapped_column(String(50), default="sepay")
    transaction_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, default=None
    )
    billing_period: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Relationships
    items: Mapped[list["InvoiceItemModel"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    user_rel: Mapped["UserModel | None"] = relationship(
        foreign_keys=[user_id],
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
            billing_period=self.billing_period,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
            items=[item.to_entity() for item in self.items],
        )

    @classmethod
    def from_entity(cls, entity: Invoice) -> "InvoiceModel":
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
            billing_period=entity.billing_period,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_deleted=entity.is_deleted,
        )


class InvoiceItemModel(SQLAlchemyTimestampMixin, Base):
    """ORM model — maps to 'invoice_items' table."""

    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    item_type: Mapped[str] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer, default=None)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(String(500), default=None)

    # Relationships
    invoice: Mapped[InvoiceModel | None] = relationship(back_populates="items")

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
    def from_entity(cls, entity: InvoiceItem) -> "InvoiceItemModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            invoice_id=entity.invoice_id,
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
