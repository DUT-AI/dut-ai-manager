from app.homework.application.dtos import HomeworkCreate
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException


class CreateHomeworkUseCase:
    """Create a new Homework record."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
    ):
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api

    async def execute(self, data: HomeworkCreate) -> HomeworkEntity:
        if not data.requires_coding and not data.requires_game:
            raise BadRequestException(
                "Vui lòng chọn ít nhất một yêu cầu cho bài tập: 'Làm bài tập coding' hoặc 'Làm game'."
            )

        extracted_slug = QuizSubmissionHelper.extract_slug(data.link, data.slug)
        if not extracted_slug:
            raise BadRequestException(
                "Bài tập bắt buộc phải có slug (hoặc đường dẫn Quiz URL hợp lệ chứa slug) để theo dõi nộp bài trên Quiz API."
            )

        # Validate with Quiz API
        metadata = await self.quiz_api.get_lesson_metadata(extracted_slug)
        if metadata is None:
            raise BadRequestException(
                f"Bài học '{extracted_slug}' không tồn tại trên hệ thống Quiz. Vui lòng kiểm tra lại slug hoặc đường dẫn."
            )

        missing_requirements: list[str] = []
        if data.requires_coding and not metadata.get("has_coding", False):
            missing_requirements.append("bài tập coding")
        if data.requires_game and not metadata.get("has_game", False):
            missing_requirements.append("câu hỏi game")

        if missing_requirements:
            missing_str = " và ".join(missing_requirements)
            lesson_name = metadata.get("name") or extracted_slug
            raise BadRequestException(
                f"Bài học '{lesson_name}' chưa có {missing_str} trên hệ thống Quiz. Vui lòng bổ sung trên Quiz trước khi giao bài."
            )

        homework = HomeworkEntity(
            title=data.title,
            deadline=data.deadline,
            link=data.link,
            slug=extracted_slug,
            requires_coding=data.requires_coding,
            requires_game=data.requires_game,
            assignee_ids=data.assignee_ids or [],
        )

        return self.homework_repo.save(homework)
