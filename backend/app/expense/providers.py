"""
Expense Module Provider — Dishka Dependency Injection.
"""

from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.expense.application.use_cases import (
    CreateExpenseUseCase,
    DeleteExpenseUseCase,
    GetExpenseByIdUseCase,
    GetExpenseSummaryUseCase,
    GetExpensesUseCase,
    UpdateExpenseStatusUseCase,
    UpdateExpenseUseCase,
)
from app.expense.infrastructure.repository import ExpenseRepository
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository


class ExpenseModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_expense_repo(self, session: Session) -> ExpenseRepository:
        return ExpenseRepository(session)

    @provide
    def create_expense_uc(
        self,
        repo: ExpenseRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
    ) -> CreateExpenseUseCase:
        return CreateExpenseUseCase(repo, user_repo, team_repo)

    @provide
    def get_expenses_uc(self, repo: ExpenseRepository) -> GetExpensesUseCase:
        return GetExpensesUseCase(repo)

    @provide
    def get_expense_by_id_uc(self, repo: ExpenseRepository) -> GetExpenseByIdUseCase:
        return GetExpenseByIdUseCase(repo)

    @provide
    def update_expense_uc(
        self,
        repo: ExpenseRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
    ) -> UpdateExpenseUseCase:
        return UpdateExpenseUseCase(repo, user_repo, team_repo)

    @provide
    def update_expense_status_uc(
        self, repo: ExpenseRepository
    ) -> UpdateExpenseStatusUseCase:
        return UpdateExpenseStatusUseCase(repo)

    @provide
    def delete_expense_uc(self, repo: ExpenseRepository) -> DeleteExpenseUseCase:
        return DeleteExpenseUseCase(repo)

    @provide
    def get_expense_summary_uc(
        self, repo: ExpenseRepository
    ) -> GetExpenseSummaryUseCase:
        return GetExpenseSummaryUseCase(repo)
