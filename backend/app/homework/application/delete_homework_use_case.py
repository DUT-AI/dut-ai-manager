from fastapi import status

from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException


class DeleteHomeworkUseCase:
    """Soft-delete a Homework record."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    def execute(self, homework_id: int) -> bool:
        existing = self.homework_repo.get_by_id(homework_id)
        if not existing:
            raise BadRequestException(
                "Homework not found", status_code=status.HTTP_404_NOT_FOUND
            )
        return self.homework_repo.delete(homework_id)
