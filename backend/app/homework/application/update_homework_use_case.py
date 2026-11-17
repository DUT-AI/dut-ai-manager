from datetime import UTC, datetime

from fastapi import status
from loguru import logger

from app.homework.application.dtos import HomeworkUpdate
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


class UpdateHomeworkUseCase:
    """Update an existing Homework record and synchronize its official coding exercises catalog."""

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

        await self._validate_requirements(
            extracted_slug, effective_coding, effective_game
        )

        now = datetime.now(UTC)
        updated = existing.model_copy(
            update={
                k: v
                for k, v in {
                    "title": data.title,
                    "link": data.link,
                    "slug": extracted_slug,
                    "requires_coding": effective_coding,
                    "requires_game": effective_game,
                    "last_synced_at": now,
                }.items()
                if v is not None
            }
        )

        saved = self.homework_repo.save(updated)
        self._sync_assignees_and_deadlines(homework_id, data)

        if effective_coding:
            await self._sync_official_exercises(homework_id, extracted_slug)
        else:
            self.homework_exercise_repo.sync_exercises(homework_id, [])

        return saved

    async def _validate_requirements(
        self,
        extracted_slug: str,
        effective_coding: bool,
        effective_game: bool,
    ) -> None:
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
                f"[UpdateHomework] Không thể đồng bộ danh mục bài tập con cho slug='{slug}': {exc}"
            )

    def _sync_assignees_and_deadlines(
        self,
        homework_id: int,
        data: HomeworkUpdate,
    ) -> None:
        if data.assignee_ids is not None:
            self.homework_assignee_repo.sync_assignees(
                homework_id,
                data.assignee_ids,
                default_deadline=data.deadline,
                force_override=data.force_override_deadlines,
            )
        elif data.deadline is not None:
            current_uids = self.homework_assignee_repo.get_assigned_user_ids(
                homework_id
            )
            if current_uids:
                self.homework_assignee_repo.assign_users(
                    homework_id,
                    current_uids,
                    deadline=data.deadline,
                    force_override=data.force_override_deadlines,
                )
