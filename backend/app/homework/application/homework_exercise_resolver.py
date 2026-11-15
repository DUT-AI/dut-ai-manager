from typing import Any

from loguru import logger

from app.homework.application.dtos import ExerciseSummaryDTO
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient


class HomeworkExerciseResolver:
    """
    Single Source of Truth cho việc phân giải danh mục các bài tập coding con của một bài tập.
    Ưu tiên lấy từ Quiz API qua slug; fallback trích xuất từ database bài nộp.
    """

    def __init__(
        self,
        quiz_api: QuizApiClient,
        homework_submission_repo: HomeworkSubmissionRepository,
    ):
        self.quiz_api = quiz_api
        self.homework_submission_repo = homework_submission_repo

    async def get_coding_exercises(
        self, homework_id: int, slug: str | None = None
    ) -> list[ExerciseSummaryDTO]:
        """Lấy danh mục các bài tập coding con dạng ExerciseSummaryDTO."""
        if slug:
            try:
                quiz_exercises = await self.quiz_api.get_lesson_exercises(slug)
                if quiz_exercises:
                    return [
                        ExerciseSummaryDTO(
                            exercise_id=str(ex["id"]),
                            title=str(ex.get("title") or f"Bài tập {idx + 1}"),
                            order_index=idx + 1,
                        )
                        for idx, ex in enumerate(quiz_exercises)
                        if isinstance(ex, dict) and "id" in ex
                    ]
            except Exception as exc:
                logger.warning(
                    f"[ExerciseResolver] Không thể lấy bài tập từ Quiz API (slug='{slug}'): {exc}"
                )

        # Fallback: Trích xuất danh mục từ các bài nộp đã lưu trong database
        submissions = self.homework_submission_repo.get_submissions_by_homework(
            homework_id
        )
        return self._extract_coding_exercises(submissions)

    async def resolve_required_exercise_ids(
        self, homework_id: int, slug: str | None = None
    ) -> set[str]:
        """Phân giải tập các mã bài tập coding con bắt buộc (set[str])."""
        exercises = await self.get_coding_exercises(homework_id, slug)
        return {ex.exercise_id for ex in exercises if ex.exercise_id}

    def _extract_coding_exercises(
        self, submissions: list[Any]
    ) -> list[ExerciseSummaryDTO]:
        """Trích xuất danh mục các bài tập con từ các bản ghi bài nộp trong DB."""
        known_exercises: dict[str, str] = {}
        for sub in submissions:
            stype = str(getattr(sub, "submission_type", "")).upper()
            ex_id = getattr(sub, "exercise_id", None)
            if (
                stype == "CODING"
                and ex_id
                and not str(ex_id).startswith("sync-legacy")
            ):
                str_ex_id = str(ex_id)
                if str_ex_id not in known_exercises:
                    known_exercises[str_ex_id] = (
                        getattr(sub, "exercise_title", "")
                        or f"Bài tập #{str_ex_id[:8]}"
                    )
                elif not known_exercises[str_ex_id] and getattr(
                    sub, "exercise_title", ""
                ):
                    known_exercises[str_ex_id] = getattr(
                        sub, "exercise_title", ""
                    )

        return [
            ExerciseSummaryDTO(
                exercise_id=ex_id,
                title=title,
                order_index=idx + 1,
            )
            for idx, (ex_id, title) in enumerate(sorted(known_exercises.items()))
        ]
