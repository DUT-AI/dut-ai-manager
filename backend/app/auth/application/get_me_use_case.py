"""Retrieve full user profile for current authenticated user."""

from app.shared.application.response import BadRequestException
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository


class GetMeUseCase:
    """Retrieve full user profile for current authenticated user."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> UserEntity:
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise BadRequestException("User not found or inactive", status_code=401)

        return user
