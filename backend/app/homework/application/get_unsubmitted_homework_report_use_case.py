from datetime import UTC, datetime

from app.homework.application.dtos import HomeworkReportResponse
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import CompletionStatus
from app.shared.domain.value_objects import UserRef
from app.user.infrastructure.repository import UserRepository


class GetUnsubmittedHomeworkReportUseCase:
    """Use case thống kê tổng hợp số lượng bài tập chưa hoàn thành của toàn bộ học viên đang hoạt động qua SSOT."""

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        user_repo: UserRepository,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.user_repo = user_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo

    async def execute(self) -> list[HomeworkReportResponse]:
        active_users = self.user_repo.get_active_users()
        if not active_users:
            return []

        now = datetime.now(UTC)
        all_homeworks = self.homework_repo.get_all()
        all_submissions = self.homework_submission_repo.get_all_submissions()

        all_hw_ids = [hw.id for hw in all_homeworks if hw.id is not None]
        exercises_by_hw = self.homework_exercise_repo.get_active_by_homework_ids(
            all_hw_ids
        )

        subs_map: dict[tuple[int, int], list] = {}
        for sub in all_submissions:
            subs_map.setdefault((sub.homework_id, sub.user_id), []).append(sub)

        reports: list[HomeworkReportResponse] = []
        for user in active_users:
            if not user.id:
                continue
            uid = user.id
            unsubmitted_count = 0

            assigned_hw_ids = self.homework_assignee_repo.get_assigned_homework_ids(uid)
            assigned_set = set(assigned_hw_ids)
            user_deadlines = (
                self.homework_assignee_repo.get_user_deadlines_for_homeworks(
                    assigned_hw_ids, uid
                )
                if assigned_hw_ids
                else {}
            )

            for hw in all_homeworks:
                if not hw.id or hw.id not in assigned_set:
                    continue

                hw_subs = subs_map.get((hw.id, uid), [])
                hw_exercises = exercises_by_hw.get(hw.id, [])
                user_dl = user_deadlines.get(hw.id)
                eval_result = hw.evaluate_submissions(
                    hw_subs,
                    required_exercises=hw_exercises,
                    deadline=user_dl,
                    reference_time=now,
                )
                if eval_result.completion_status != CompletionStatus.COMPLETED:
                    unsubmitted_count += 1

            reports.append(
                HomeworkReportResponse(
                    user_id=uid,
                    owner=UserRef(
                        id=user.id,
                        name=user.name,
                        email=user.email,
                        avatar_url=user.avatar_url,
                    ),
                    unsubmitted_count=unsubmitted_count,
                )
            )

        reports.sort(key=lambda r: r.unsubmitted_count, reverse=True)
        return reports
