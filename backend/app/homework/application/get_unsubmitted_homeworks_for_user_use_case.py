from datetime import UTC, datetime

from app.homework.application.dtos import HomeworkResponse
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import CompletionStatus


class GetUnsubmittedHomeworksForUserUseCase:
    """Use case lấy danh sách bài tập chưa hoàn thành của một học viên cụ thể qua SSOT."""

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo

    async def execute(self, user_id: int) -> list[HomeworkResponse]:
        assigned_homeworks = self.homework_repo.get_all_assigned_to_user(
            user_id=user_id, deleted=False
        )
        if not assigned_homeworks:
            return []

        now = datetime.now(UTC)
        hw_ids = [hw.id for hw in assigned_homeworks if hw.id is not None]

        user_submissions = (
            self.homework_submission_repo.get_user_submissions_for_homeworks(
                homework_ids=hw_ids, user_id=user_id
            )
        )
        user_deadlines = self.homework_assignee_repo.get_user_deadlines_for_homeworks(
            hw_ids, user_id
        )
        exercises_by_hw = self.homework_exercise_repo.get_active_by_homework_ids(hw_ids)

        submissions_by_hw: dict[int, list] = {}
        for sub in user_submissions:
            submissions_by_hw.setdefault(sub.homework_id, []).append(sub)

        unsubmitted: list[HomeworkResponse] = []
        for hw in assigned_homeworks:
            assert hw.id is not None
            hw_subs = submissions_by_hw.get(hw.id, [])
            user_dl = user_deadlines.get(hw.id)
            hw_exercises = exercises_by_hw.get(hw.id, [])

            eval_result = hw.evaluate_submissions(
                hw_subs,
                required_exercises=hw_exercises,
                deadline=user_dl,
                reference_time=now,
            )
            if eval_result.completion_status != CompletionStatus.COMPLETED:
                unsubmitted.append(
                    HomeworkResponse.from_evaluation(hw, eval_result, deadline=user_dl)
                )

        return unsubmitted
