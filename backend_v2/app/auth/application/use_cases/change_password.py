from app.auth.application.dtos import ChangePasswordRequestDTO
from app.auth.domain.exceptions import InvalidCredentialsException
from app.auth.domain.interfaces import IAuthUserRepository, IPasswordHasher


class ChangePasswordUseCase:
    def __init__(
        self,
        auth_repo: IAuthUserRepository,
        password_hasher: IPasswordHasher,
    ):
        self.auth_repo = auth_repo
        self.password_hasher = password_hasher

    async def execute(self, user_id: int, payload: ChangePasswordRequestDTO) -> None:
        user = await self.auth_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentialsException(message="User không tồn tại")

        if not user.hashed_password or not self.password_hasher.verify(
            payload.old_password, user.hashed_password
        ):
            raise InvalidCredentialsException(message="Mật khẩu cũ không chính xác")

        new_hashed_password = self.password_hasher.hash(payload.new_password)
        await self.auth_repo.update_password(user_id, new_hashed_password)
