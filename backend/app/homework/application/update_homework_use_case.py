from fastapi import status

from app.homework.application.dtos import HomeworkUpdate
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException


class UpdateHomeworkUseCase:
    """Update an existing Homework record."""

    def __init__(self, homework_repo: HomeworkRepository):
        self.homework_repo = homework_repo

    async def execute(
        self,
        homework_id: int,
        data: HomeworkUpdate,
    ) -> HomeworkEntity:
        existing = self.homework_repo.get_by_id(homework_id)
        if not existing:
            raise BadRequestException(
                "Homework not found", status_code=status.HTTP_404_NOT_FOUND
            )

        effective_link = data.link if data.link is not None else existing.link
        effective_slug = data.slug if data.slug is not None else existing.slug
        extracted_slug = QuizSubmissionHelper.extract_slug(effective_link, effective_slug)

        if not extracted_slug:
            raise BadRequestException(
                "Bài tập bắt buộc phải có slug (hoặc đường dẫn Quiz URL hợp lệ chứa slug) để theo dõi nộp bài trên Quiz API."
            )

        updated = existing.model_copy(
            update={
                k: v
                for k, v in {
                    "title": data.title,
                    "deadline": data.deadline,
                    "link": data.link,
                    "slug": extracted_slug,
                    "assignee_ids": data.assignee_ids,
                }.items()
                if v is not None
            }
        )

        return self.homework_repo.save(updated)
