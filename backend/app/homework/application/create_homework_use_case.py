from app.homework.application.dtos import HomeworkCreate
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException


class CreateHomeworkUseCase:
    """Create a new Homework record."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    async def execute(self, data: HomeworkCreate) -> HomeworkEntity:
        extracted_slug = QuizSubmissionHelper.extract_slug(data.link, data.slug)
        if not extracted_slug:
            raise BadRequestException(
                "Bài tập bắt buộc phải có slug (hoặc đường dẫn Quiz URL hợp lệ chứa slug) để theo dõi nộp bài trên Quiz API."
            )

        homework = HomeworkEntity(
            title=data.title,
            deadline=data.deadline,
            link=data.link,
            slug=extracted_slug,
            assignee_ids=data.assignee_ids or [],
        )

        return self.homework_repo.save(homework)
