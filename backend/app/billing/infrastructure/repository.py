"""
Billing Repository — data access layer.
"""

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.billing.domain.entity import Invoice
from app.billing.infrastructure.model import InvoiceItemModel, InvoiceModel
from app.shared.infrastructure.base_repository import BaseRepository


class InvoiceRepository(BaseRepository[InvoiceModel, Invoice]):
    """Concrete repository for Invoices."""

    def __init__(self, session: Session):
        super().__init__(session, InvoiceModel)

    def get_by_reference_code(self, reference_code: str) -> Invoice | None:
        """Find an invoice by its unique reference code."""
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.reference_code == reference_code)
            .options(joinedload(InvoiceModel.items))
        )
        result = self.session.scalars(statement).unique().first()
        return result.to_entity() if result else None

    def get_by_user_id(self, user_id: int) -> list[Invoice]:
        """Get all invoices for a specific user."""
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.user_id == user_id)
            .where(InvoiceModel.is_deleted == False)  # noqa: E712
            .options(joinedload(InvoiceModel.items))
            .order_by(desc(InvoiceModel.created_at))
        )
        return [m.to_entity() for m in self.session.scalars(statement).unique().all()]

    def get_all_active(self, skip: int = 0, limit: int = 100) -> list[Invoice]:
        """Get all active invoices with items."""
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.is_deleted == False)  # noqa: E712
            .options(joinedload(InvoiceModel.items))
            .order_by(desc(InvoiceModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        return [m.to_entity() for m in self.session.scalars(statement).unique().all()]

    def get_matrix_report(
        self,
        start_date: datetime,
        end_date: datetime,
        user_ids: list[int] | None = None,
    ) -> list[Invoice]:
        """Get invoices for report filtering by date and users."""
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.is_deleted == False)  # noqa: E712
            .where(InvoiceModel.created_at >= start_date)
            .where(InvoiceModel.created_at <= end_date)
            .options(joinedload(InvoiceModel.items))
        )
        if user_ids:
            statement = statement.where(InvoiceModel.user_id.in_(user_ids))

        statement = statement.order_by(InvoiceModel.user_id, InvoiceModel.created_at)
        return [m.to_entity() for m in self.session.scalars(statement).unique().all()]

    def save_invoice(self, invoice: Invoice) -> Invoice:
        """
        Save invoice and its items.
        """
        if invoice.id:
            # Update existing
            db_model = self.session.get(InvoiceModel, invoice.id)
            if not db_model:
                raise ValueError(f"Invoice {invoice.id} not found")

            # Update fields
            db_model.status = invoice.status
            db_model.transaction_id = invoice.transaction_id
            db_model.description = invoice.description
            db_model.amount = invoice.amount

            # Replace items
            db_model.items = [
                InvoiceItemModel.from_entity(item) for item in invoice.items
            ]

            self.session.add(db_model)
            self.session.flush()
            self.session.refresh(db_model)
            return db_model.to_entity()
        else:
            # Create new
            db_model = InvoiceModel.from_entity(invoice)
            db_model.items = [
                InvoiceItemModel.from_entity(item) for item in invoice.items
            ]

            self.session.add(db_model)
            self.session.flush()
            self.session.refresh(db_model)
            return db_model.to_entity()
