from fastapi import HTTPException

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.infrastructure.repository import UserRepository


class DeleteUserUseCase:
    """Use case for deleting (removing) a user."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int) -> bool:
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=user_id)
            ]
        )
        user = self.repo.get_one(qs)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        self.repo.soft_delete(user)
        return True
