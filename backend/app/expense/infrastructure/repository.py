"""
Expense Repository — SQLAlchemy 2.0 infrastructure layer.
"""

from collections.abc import Sequence

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, joinedload

from app.expense.domain.entity import ExpenseInvoice, ExpenseStatus
from app.expense.infrastructure.model import ExpenseInvoiceModel


class ExpenseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, entity: ExpenseInvoice) -> ExpenseInvoice:
        model = ExpenseInvoiceModel.from_entity(entity)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model.to_entity()

    def get_by_id(self, expense_id: str) -> ExpenseInvoiceModel | None:
        stmt = (
            select(ExpenseInvoiceModel)
            .options(
                joinedload(ExpenseInvoiceModel.spender),
                joinedload(ExpenseInvoiceModel.team),
            )
            .where(
                ExpenseInvoiceModel.id == expense_id,
                ExpenseInvoiceModel.is_deleted == False,
            )
        )
        return self.session.scalar(stmt)

    def get_all(
        self,
        month: int | None = None,
        year: int | None = None,
        status: ExpenseStatus | str | None = None,
        spender_id: int | None = None,
        team_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ExpenseInvoiceModel]:
        stmt = (
            select(ExpenseInvoiceModel)
            .options(
                joinedload(ExpenseInvoiceModel.spender),
                joinedload(ExpenseInvoiceModel.team),
            )
            .where(ExpenseInvoiceModel.is_deleted == False)
        )

        if month is not None:
            stmt = stmt.where(
                extract("month", ExpenseInvoiceModel.expense_date) == month
            )
        if year is not None:
            stmt = stmt.where(extract("year", ExpenseInvoiceModel.expense_date) == year)
        if status is not None:
            status_str = status.value if isinstance(status, ExpenseStatus) else status
            stmt = stmt.where(ExpenseInvoiceModel.status == status_str)
        if spender_id is not None:
            stmt = stmt.where(ExpenseInvoiceModel.spender_id == spender_id)
        if team_id is not None:
            stmt = stmt.where(ExpenseInvoiceModel.team_id == team_id)

        stmt = stmt.order_by(
            ExpenseInvoiceModel.expense_date.desc(),
            ExpenseInvoiceModel.created_at.desc(),
        )
        stmt = stmt.offset(offset).limit(limit)

        return self.session.scalars(stmt).all()

    def get_summary(
        self,
        month: int | None = None,
        year: int | None = None,
        spender_id: int | None = None,
        team_id: int | None = None,
    ) -> dict[str, int]:
        stmt = select(
            ExpenseInvoiceModel.status,
            func.coalesce(func.sum(ExpenseInvoiceModel.amount), 0),
        ).where(ExpenseInvoiceModel.is_deleted == False)

        if month is not None:
            stmt = stmt.where(
                extract("month", ExpenseInvoiceModel.expense_date) == month
            )
        if year is not None:
            stmt = stmt.where(extract("year", ExpenseInvoiceModel.expense_date) == year)
        if spender_id is not None:
            stmt = stmt.where(ExpenseInvoiceModel.spender_id == spender_id)
        if team_id is not None:
            stmt = stmt.where(ExpenseInvoiceModel.team_id == team_id)

        stmt = stmt.group_by(ExpenseInvoiceModel.status)
        results = self.session.execute(stmt).all()

        summary = {"total_paid": 0, "total_unpaid": 0, "total": 0}
        for status_val, total_amount in results:
            if status_val == ExpenseStatus.PAID.value:
                summary["total_paid"] = int(total_amount)
            elif status_val == ExpenseStatus.UNPAID.value:
                summary["total_unpaid"] = int(total_amount)
        summary["total"] = summary["total_paid"] + summary["total_unpaid"]
        return summary

    def update(self, model: ExpenseInvoiceModel) -> ExpenseInvoiceModel:
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def delete(self, expense_id: str) -> bool:
        model = self.get_by_id(expense_id)
        if not model:
            return False
        model.is_deleted = True
        self.session.add(model)
        self.session.commit()
        return True
