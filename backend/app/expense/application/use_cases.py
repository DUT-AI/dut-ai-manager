"""
Expense Application Use Cases — business logic layer.
"""

import uuid
from collections.abc import Sequence
from datetime import date

from app.expense.domain.entity import ExpenseInvoice, ExpenseStatus
from app.expense.infrastructure.model import ExpenseInvoiceModel
from app.expense.infrastructure.repository import ExpenseRepository
from app.shared.application.response import BadRequestException
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class CreateExpenseUseCase:
    def __init__(
        self,
        repo: ExpenseRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
    ):
        self.repo = repo
        self.user_repo = user_repo
        self.team_repo = team_repo

    def execute(
        self,
        expense_date: date,
        amount: int,
        description: str,
        spender_id: int,
        team_id: int,
        status: ExpenseStatus = ExpenseStatus.UNPAID,
        payment_date: date | None = None,
        note: str | None = None,
        created_by: int | None = None,
    ) -> ExpenseInvoiceModel:
        # Check user exists
        user = self.user_repo.get_by_id(spender_id)
        if not user:
            raise BadRequestException(f"Người chi với ID {spender_id} không tồn tại")

        # Check team exists
        team = self.team_repo.get_by_id(team_id)
        if not team:
            raise BadRequestException(f"Nhóm với ID {team_id} không tồn tại")

        if amount <= 0:
            raise BadRequestException("Số tiền phải lớn hơn 0")

        if status == ExpenseStatus.PAID and payment_date is None:
            payment_date = expense_date

        entity = ExpenseInvoice(
            id=str(uuid.uuid4()),
            expense_date=expense_date,
            amount=amount,
            description=description,
            spender_id=spender_id,
            team_id=team_id,
            status=status,
            payment_date=payment_date if status == ExpenseStatus.PAID else None,
            note=note,
            created_by=created_by,
        )
        self.repo.create(entity)
        result = self.repo.get_by_id(entity.id)
        if not result:
            raise BadRequestException("Không thể tạo hóa đơn xuất ra")
        return result


class GetExpensesUseCase:
    def __init__(self, repo: ExpenseRepository):
        self.repo = repo

    def execute(
        self,
        month: int | None = None,
        year: int | None = None,
        status: ExpenseStatus | None = None,
        spender_id: int | None = None,
        team_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ExpenseInvoiceModel]:
        return self.repo.get_all(
            month=month,
            year=year,
            status=status,
            spender_id=spender_id,
            team_id=team_id,
            limit=limit,
            offset=offset,
        )


class GetExpenseByIdUseCase:
    def __init__(self, repo: ExpenseRepository):
        self.repo = repo

    def execute(self, expense_id: str) -> ExpenseInvoiceModel:
        expense = self.repo.get_by_id(expense_id)
        if not expense:
            raise BadRequestException("Không tìm thấy hóa đơn xuất ra")
        return expense


class UpdateExpenseUseCase:
    def __init__(
        self,
        repo: ExpenseRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
    ):
        self.repo = repo
        self.user_repo = user_repo
        self.team_repo = team_repo

    def execute(
        self,
        expense_id: str,
        expense_date: date | None = None,
        amount: int | None = None,
        description: str | None = None,
        spender_id: int | None = None,
        team_id: int | None = None,
        status: ExpenseStatus | None = None,
        payment_date: date | None = None,
        note: str | None = None,
        updated_by: int | None = None,
    ) -> ExpenseInvoiceModel:
        model = self.repo.get_by_id(expense_id)
        if not model:
            raise BadRequestException("Không tìm thấy hóa đơn xuất ra")

        if spender_id is not None:
            user = self.user_repo.get_by_id(spender_id)
            if not user:
                raise BadRequestException(
                    f"Người chi với ID {spender_id} không tồn tại"
                )
            model.spender_id = spender_id

        if team_id is not None:
            team = self.team_repo.get_by_id(team_id)
            if not team:
                raise BadRequestException(f"Nhóm với ID {team_id} không tồn tại")
            model.team_id = team_id

        if expense_date is not None:
            model.expense_date = expense_date

        if amount is not None:
            if amount <= 0:
                raise BadRequestException("Số tiền phải lớn hơn 0")
            model.amount = amount

        if description is not None:
            model.description = description

        if note is not None:
            model.note = note

        if status is not None:
            model.status = status.value if isinstance(status, ExpenseStatus) else status
            if (
                status == ExpenseStatus.PAID
                and payment_date is None
                and model.payment_date is None
            ):
                model.payment_date = model.expense_date
            elif status == ExpenseStatus.UNPAID:
                model.payment_date = None

        if payment_date is not None:
            model.payment_date = payment_date

        model.updated_by = updated_by
        model.updated_at = get_current_utc7_time()

        self.repo.update(model)
        result = self.repo.get_by_id(expense_id)
        if not result:
            raise BadRequestException("Lỗi khi cập nhật hóa đơn xuất ra")
        return result


class UpdateExpenseStatusUseCase:
    def __init__(self, repo: ExpenseRepository):
        self.repo = repo

    def execute(
        self,
        expense_id: str,
        status: ExpenseStatus,
        payment_date: date | None = None,
        updated_by: int | None = None,
    ) -> ExpenseInvoiceModel:
        model = self.repo.get_by_id(expense_id)
        if not model:
            raise BadRequestException("Không tìm thấy hóa đơn xuất ra")

        model.status = status.value if isinstance(status, ExpenseStatus) else status
        if status == ExpenseStatus.PAID:
            model.payment_date = (
                payment_date or model.expense_date or get_current_utc7_time().date()
            )
        else:
            model.payment_date = None

        model.updated_by = updated_by
        model.updated_at = get_current_utc7_time()

        self.repo.update(model)
        result = self.repo.get_by_id(expense_id)
        if not result:
            raise BadRequestException("Lỗi khi cập nhật trạng thái hóa đơn")
        return result


class DeleteExpenseUseCase:
    def __init__(self, repo: ExpenseRepository):
        self.repo = repo

    def execute(self, expense_id: str) -> bool:
        model = self.repo.get_by_id(expense_id)
        if not model:
            raise BadRequestException("Không tìm thấy hóa đơn xuất ra")
        return self.repo.delete(expense_id)


class GetExpenseSummaryUseCase:
    def __init__(self, repo: ExpenseRepository):
        self.repo = repo

    def execute(
        self,
        month: int | None = None,
        year: int | None = None,
        spender_id: int | None = None,
        team_id: int | None = None,
    ) -> dict[str, int]:
        return self.repo.get_summary(
            month=month, year=year, spender_id=spender_id, team_id=team_id
        )
