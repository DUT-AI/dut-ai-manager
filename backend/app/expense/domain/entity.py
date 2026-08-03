"""
Expense Domain Entities — pure Pydantic, NO ORM dependency.
"""

import uuid
from datetime import date
from enum import Enum

from pydantic import Field

from app.shared.domain.base_entity import BaseEntity


class ExpenseStatus(str, Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"


class ExpenseInvoice(BaseEntity):
    """Domain entity representing an outgoing expense invoice."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expense_date: date
    amount: int
    description: str
    spender_id: int
    team_id: int
    status: ExpenseStatus = ExpenseStatus.UNPAID
    payment_date: date | None = None
    note: str | None = None
