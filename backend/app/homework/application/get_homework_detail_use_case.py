from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.homework_repository import HomeworkRepository


class GetHomeworkDetailUseCase:
    """Use case lấy thông tin chi tiết một bài tập theo ID."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    def execute(self, homework_id: int) -> HomeworkEntity | None:
        return self.homework_repo.get_by_id(homework_id)
