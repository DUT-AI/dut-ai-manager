"""
Billing Repository — data access layer.
"""

from typing import List, Optional, Any, cast

from app.billing.domain.entity import Invoice
from app.billing.infrastructure.model import InvoiceModel, InvoiceItemModel
from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select


class InvoiceRepository(BaseRepository[InvoiceModel, Invoice]):
    """Concrete repository for Invoices."""

    def __init__(self, session: Session):
        super().__init__(session, InvoiceModel)

    def get_by_reference_code(self, reference_code: str) -> Optional[Invoice]:
        """Find an invoice by its unique reference code."""
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.reference_code == reference_code)
            .options(joinedload(cast(Any, InvoiceModel.items)))
        )
        result = self.session.exec(statement).unique().first()
        return result.to_entity() if result else None

    def get_by_user_id(self, user_id: int) -> List[Invoice]:
        """Get all invoices for a specific user."""
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.user_id == user_id)
            .where(InvoiceModel.is_deleted == False)  # noqa: E712
            .options(joinedload(cast(Any, InvoiceModel.items)))
            .order_by(desc(cast(Any, InvoiceModel.created_at)))
        )
        return [m.to_entity() for m in self.session.exec(statement).unique().all()]

    def get_all_active(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all active invoices with items."""
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.is_deleted == False)  # noqa: E712
            .options(joinedload(cast(Any, InvoiceModel.items)))
            .order_by(desc(cast(Any, InvoiceModel.created_at)))
            .offset(skip)
            .limit(limit)
        )
        return [m.to_entity() for m in self.session.exec(statement).unique().all()]

    def save_invoice(self, invoice: Invoice) -> Invoice:
        """
        Save invoice and its items.
        """
        if invoice.id:
            # Update existing
            db_model = self.session.get(InvoiceModel, invoice.id)
            if not db_model:
                raise ValueError(f"Invoice {invoice.id} not found")
            
            # Simple fields update
            db_model.status = invoice.status
            db_model.transaction_id = invoice.transaction_id
            
            self.session.add(db_model)
            self.session.flush()
            return db_model.to_entity()
        else:
            # Create new
            db_model = InvoiceModel.from_entity(invoice)
            db_model.items = [InvoiceItemModel.from_entity(item) for item in invoice.items]
            
            self.session.add(db_model)
            self.session.flush()
            self.session.refresh(db_model)
            return db_model.to_entity()
