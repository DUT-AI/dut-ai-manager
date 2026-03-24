from app.user.domain.exceptions import UserNotFoundException
from app.user.domain.repository import IUserRepository


class DeleteUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int) -> None:
        user = await self.user_repo.get_by(user_id=user_id)
        if not user:
            raise UserNotFoundException(user_id)

        await self.user_repo.delete(user_id)
