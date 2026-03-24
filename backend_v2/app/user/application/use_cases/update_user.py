from app.user.application.dtos import UserSettingsUpdateDTO, UserUpdateDTO
from app.user.domain.exceptions import UserNotFoundException
from app.user.domain.repository import IUserRepository
from app.user.domain.user_entity import User
from fastapi import UploadFile


class UpdateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int, user_data: UserUpdateDTO) -> User:
        user = await self.user_repo.get_by(user_id=user_id)
        if not user:
            raise UserNotFoundException(user_id)

        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        return await self.user_repo.update(user)


class UpdateUserSettingsUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int, settings_data: UserSettingsUpdateDTO) -> User:
        user = await self.user_repo.get_by(user_id=user_id)
        if not user:
            raise UserNotFoundException(user_id)

        user.update_settings(
            avatar_url=settings_data.avatar_url, discord_id=settings_data.discord_id
        )
        return await self.user_repo.update(user)


class UpdateUserAvatarUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int, file: UploadFile) -> User:
        user = await self.user_repo.get_by(user_id=user_id)
        if not user:
            raise UserNotFoundException(user_id)

        # In a real app, you would inject a Storage Port here.
        # For now, we mock the uploaded URL.
        file_url = f"https://mock-storage.dut-ai.com/{file.filename}"
        user.update_settings(avatar_url=file_url)

        return await self.user_repo.update(user)
