from datetime import UTC, datetime

from loguru import logger

from app.homework.application.dtos import HomeworkCreate
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkExercise
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.application.response import BadRequestException


class CreateHomeworkUseCase:
    """Create a new Homework record and initialize its official coding exercises catalog."""

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        quiz_api: QuizApiClient,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
    ):
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo

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

        now = datetime.now(UTC)
        homework = HomeworkEntity(
            title=data.title,
            link=data.link,
            slug=extracted_slug,
            requires_coding=data.requires_coding,
            requires_game=data.requires_game,
            last_synced_at=now,
        )

        saved = self.homework_repo.save(homework)
        target_id = saved.id or homework.id
        if target_id and data.assignee_ids:
            self.homework_assignee_repo.assign_users(
                target_id, data.assignee_ids, deadline=data.deadline
            )

        if target_id and data.requires_coding:
            await self._sync_official_exercises(target_id, extracted_slug)

        return saved

    async def _sync_official_exercises(self, homework_id: int, slug: str) -> None:
        try:
            quiz_exercises = await self.quiz_api.get_lesson_exercises(slug)
            if quiz_exercises is not None:
                entities = [
                    HomeworkExercise(
                        homework_id=homework_id,
                        exercise_id=str(ex["id"]),
                        title=str(ex.get("title") or f"Bài tập {idx + 1}"),
                        order_index=idx + 1,
                        is_active=True,
                    )
                    for idx, ex in enumerate(quiz_exercises)
                    if isinstance(ex, dict) and ex.get("id")
                ]
                self.homework_exercise_repo.sync_exercises(homework_id, entities)
        except Exception as exc:
            logger.warning(
                f"[CreateHomework] Không thể khởi tạo danh mục bài tập con cho slug='{slug}': {exc}"
            )
