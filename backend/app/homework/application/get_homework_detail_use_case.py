from typing import Any

from app.homework.application.dtos import (
    ExerciseSummaryDTO,
    HomeworkResponseDetail,
)
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient


class GetHomeworkDetailUseCase:
    """Use case lấy thông tin chi tiết một bài tập theo ID bao gồm danh sách assignee_ids và danh mục bài tập con."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        quiz_api: QuizApiClient,
        homework_submission_repo: HomeworkSubmissionRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.quiz_api = quiz_api
        self.homework_submission_repo = homework_submission_repo

    async def execute(self, homework_id: int) -> HomeworkResponseDetail | None:
        hw = self.homework_repo.get_by_id(homework_id)
        if not hw:
            return None
        assignees = self.homework_assignee_repo.get_assignees_with_user_info(
            homework_id
        )
        assignee_ids = sorted([a.user_id for a in assignees])
        deadlines = [a.deadline for a in assignees if a.deadline]
        min_dl = min(deadlines) if deadlines else None

        coding_exercises: list[ExerciseSummaryDTO] = []
        if hw.requires_coding:
            coding_exercises = await self._get_coding_exercises(hw)

        return HomeworkResponseDetail.from_domain(
            hw,
            assignee_ids=assignee_ids,
            deadline=min_dl,
            coding_exercises=coding_exercises,
        )

    async def _get_coding_exercises(self, hw: Any) -> list[ExerciseSummaryDTO]:
        """Lấy danh mục các bài tập coding con từ Quiz API hoặc trích xuất từ database bài nộp."""
        if hw.slug:
            try:
                quiz_exercises = await self.quiz_api.get_lesson_exercises(hw.slug)
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
            except Exception:
                pass

        submissions = self.homework_submission_repo.get_submissions_by_homework(
            hw.id
        )
        return self._extract_coding_exercises(submissions)

    def _extract_coding_exercises(
        self, submissions: list[Any]
    ) -> list[ExerciseSummaryDTO]:
        """Trích xuất danh mục các bài tập coding con từ các bài nộp đã lưu."""
        known_exercises: dict[str, str] = {}
        for sub in submissions:
            stype = str(getattr(sub, "submission_type", "")).upper()
            ex_id = getattr(sub, "exercise_id", None)
            if stype == "CODING" and ex_id:
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
                title=title or f"Bài tập {idx + 1}",
                order_index=idx + 1,
            )
            for idx, (ex_id, title) in enumerate(sorted(known_exercises.items()))
        ]
