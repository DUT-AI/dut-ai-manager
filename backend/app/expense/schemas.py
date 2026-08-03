"""
Expense Schemas — Pydantic request/response models.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.expense.domain.entity import ExpenseStatus


class ExpenseSpenderInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class ExpenseTeamInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_name: str


class ExpenseInvoiceCreate(BaseModel):
    expense_date: date
    amount: int
    description: str
    spender_id: int
    team_id: int
    status: ExpenseStatus = ExpenseStatus.UNPAID
    payment_date: date | None = None
    note: str | None = None


class ExpenseInvoiceUpdate(BaseModel):
    expense_date: date | None = None
    amount: int | None = None
    description: str | None = None
    spender_id: int | None = None
    team_id: int | None = None
    status: ExpenseStatus | None = None
    payment_date: date | None = None
    note: str | None = None


class ExpenseInvoiceStatusUpdate(BaseModel):
    status: ExpenseStatus
    payment_date: date | None = None


class ExpenseInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    expense_date: date
    amount: int
    description: str
    spender_id: int
    team_id: int
    status: ExpenseStatus
    payment_date: date | None = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime
    spender: ExpenseSpenderInfo | None = None
    team: ExpenseTeamInfo | None = None


class ExpenseSummaryResponse(BaseModel):
    total_paid: int
    total_unpaid: int
    total: int
