from app.user.application.dtos import UserImportResultDTO
from app.user.domain.repository import IUserRepository
from fastapi import UploadFile


class ImportUsersUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, file: UploadFile) -> UserImportResultDTO:
        # Mock logic to parse Excel file, this would normally use an infrastructure service.
        return UserImportResultDTO(total=1, success_count=1, error_count=0, errors=[])
