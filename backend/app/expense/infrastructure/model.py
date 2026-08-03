"""
Expense ORM Models — SQLAlchemy 2.0, infrastructure layer.
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.expense.domain.entity import ExpenseInvoice, ExpenseStatus
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.utils.datetime import get_current_utc7_time

if TYPE_CHECKING:
    from app.team.infrastructure.model import TeamModel
    from app.user.infrastructure.model import UserModel


class ExpenseInvoiceModel(SQLAlchemyTimestampMixin, Base):
    """ORM model — maps to 'outgoing_invoices' table."""

    __tablename__ = "outgoing_invoices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    spender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=ExpenseStatus.UNPAID, index=True
    )
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)

    # Relationships
    spender: Mapped["UserModel | None"] = relationship(
        foreign_keys=[spender_id],
    )
    team: Mapped["TeamModel | None"] = relationship(
        foreign_keys=[team_id],
    )

    def to_entity(self) -> ExpenseInvoice:
        """ORM Model → Domain Entity."""
        return ExpenseInvoice(
            id=self.id,
            expense_date=self.expense_date,
            amount=self.amount,
            description=self.description,
            spender_id=self.spender_id,
            team_id=self.team_id,
            status=ExpenseStatus(self.status),
            payment_date=self.payment_date,
            note=self.note,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: ExpenseInvoice) -> "ExpenseInvoiceModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id or str(uuid.uuid4()),
            expense_date=entity.expense_date,
            amount=entity.amount,
            description=entity.description,
            spender_id=entity.spender_id,
            team_id=entity.team_id,
            status=entity.status.value
            if isinstance(entity.status, ExpenseStatus)
            else entity.status,
            payment_date=entity.payment_date,
            note=entity.note,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_deleted=entity.is_deleted,
        )
