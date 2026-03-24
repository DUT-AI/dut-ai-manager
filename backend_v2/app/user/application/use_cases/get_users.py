from typing import List

from app.user.domain.exceptions import UserNotFoundException
from app.user.domain.repository import IUserRepository
from app.user.domain.user_entity import User, UserStatus


class GetUsersUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(
        self,
        limit: int = 100,
        offset=0,
        search: str | None = None,
        role: str | None = None,
        status: UserStatus | None = None,
    ) -> List[User]:
        return await self.user_repo.list(
            limit=limit, offset=offset, search=search, role=role, status=status
        )


class GetUserByIdUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int) -> User:
        user = await self.user_repo.get_by(user_id=user_id)
        if not user:
            raise UserNotFoundException(user_id)
        return user
