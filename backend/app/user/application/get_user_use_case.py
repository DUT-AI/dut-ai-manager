from fastapi import HTTPException

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.repository import UserRepository


class GetUserUseCase:
    """Use case for retrieving user information."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int) -> UserEntity:
        # Load đầy đủ role/permissions
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=user_id)
            ],
            include=[
                "roles",
                "roles.role_permissions",
                "roles.role_permissions.permission",
            ],
        )
        user = self.repo.get_one(qs)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_all(self) -> list[UserEntity]:
        # Mặc định load đầy đủ role/permissions để to_entity chính xác
        qs = build_query_support(
            include=[
                "roles",
                "roles.role_permissions",
                "roles.role_permissions.permission",
            ]
        )
        return self.repo.get_all(qs)

    def search(self, keyword: str) -> list[UserEntity]:
        return self.repo.search_user(keyword)

    def get_paged(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        role: str | None = None,
        status: UserStatus | None = None,
    ) -> tuple[list[UserEntity], int]:
        return self.repo.get_paged_users(
            page=page,
            page_size=page_size,
            keyword=keyword,
            role=role,
            status=status,
        )

    def get_active_users(self) -> list[UserEntity]:
        return self.repo.get_active_users()
