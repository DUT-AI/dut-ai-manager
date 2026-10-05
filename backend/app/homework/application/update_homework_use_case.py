from fastapi import status

from app.homework.application.dtos import HomeworkUpdate
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException


class UpdateHomeworkUseCase:
    """Update an existing Homework record."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
    ):
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api

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

        effective_coding = (
            data.requires_coding
            if data.requires_coding is not None
            else existing.requires_coding
        )
        effective_game = (
            data.requires_game
            if data.requires_game is not None
            else existing.requires_game
        )

        if not effective_coding and not effective_game:
            raise BadRequestException(
                "Vui lòng chọn ít nhất một yêu cầu cho bài tập: 'Làm bài tập coding' hoặc 'Làm game'."
            )

        effective_link = data.link if data.link is not None else existing.link
        effective_slug = data.slug if data.slug is not None else existing.slug
        extracted_slug = QuizSubmissionHelper.extract_slug(
            effective_link, effective_slug
        )

        if not extracted_slug:
            raise BadRequestException(
                "Bài tập bắt buộc phải có slug (hoặc đường dẫn Quiz URL hợp lệ chứa slug) để theo dõi nộp bài trên Quiz API."
            )

        # Validate with Quiz API if slug or requirements changed
        metadata = await self.quiz_api.get_lesson_metadata(extracted_slug)
        if metadata is None:
            raise BadRequestException(
                f"Bài học '{extracted_slug}' không tồn tại trên hệ thống Quiz. Vui lòng kiểm tra lại slug hoặc đường dẫn."
            )

        missing_requirements: list[str] = []
        if effective_coding and not metadata.get("has_coding", False):
            missing_requirements.append("bài tập coding")
        if effective_game and not metadata.get("has_game", False):
            missing_requirements.append("câu hỏi game")

        if missing_requirements:
            missing_str = " và ".join(missing_requirements)
            lesson_name = metadata.get("name") or extracted_slug
            raise BadRequestException(
                f"Bài học '{lesson_name}' chưa có {missing_str} trên hệ thống Quiz. Vui lòng bổ sung trên Quiz trước khi giao bài."
            )

        updated = existing.model_copy(
            update={
                k: v
                for k, v in {
                    "title": data.title,
                    "deadline": data.deadline,
                    "link": data.link,
                    "slug": extracted_slug,
                    "requires_coding": data.requires_coding,
                    "requires_game": data.requires_game,
                    "assignee_ids": data.assignee_ids,
                }.items()
                if v is not None
            }
        )

        return self.homework_repo.save(updated)

