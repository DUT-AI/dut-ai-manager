"""
Homework Task Scanner.
Scans upcoming homeworks and filters out completed submissions via SSOT.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.homework.domain.entity import Homework, HomeworkExercise
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import AssigneeUserInfo
from app.reminder.application.scanners.base_scanner import (
    BaseTaskScanner,
    ScannedCandidateTask,
    calculate_matching_stages,
)
from app.reminder.domain.entity import TaskType
from app.shared.domain.datetime_types import ensure_utc


class HomeworkTaskScanner(BaseTaskScanner):
    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_exercise_repo = homework_exercise_repo

    def scan_pending_tasks(self, now: datetime) -> list[ScannedCandidateTask]:
        candidates: list[ScannedCandidateTask] = []
        all_homeworks = self.homework_repo.get_all(limit=200)

        hw_ids = [hw.id for hw in all_homeworks if hw.id is not None]
        exercises_by_hw = self.homework_exercise_repo.get_active_by_homework_ids(hw_ids)

        now_utc = ensure_utc(now)

        for hw in all_homeworks:
            if not hw.id:
                continue

            assignees = self.homework_assignee_repo.get_assignees_with_user_info(hw.id)
            if not assignees:
                continue

            hw_exercises = exercises_by_hw.get(hw.id, [])

            for assignee in assignees:
                candidate = self._evaluate_assignee_candidate(
                    hw=hw,
                    assignee=assignee,
                    now_utc=now_utc,
                    hw_exercises=hw_exercises,
                )
                if candidate:
                    candidates.append(candidate)

        return candidates

    def _normalize_deadline(self, deadline: datetime) -> datetime:
        """Chuẩn hóa deadline về UTC, nếu là mốc 00:00:00 thì quy về cuối ngày 23:59:59 (Asia/Ho_Chi_Minh)."""
        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        dt = ensure_utc(deadline)
        local_dt = dt.astimezone(vn_tz)
        if local_dt.hour == 0 and local_dt.minute == 0 and local_dt.second == 0:
            return local_dt.replace(hour=23, minute=59, second=59).astimezone(UTC)
        return dt

    def _evaluate_assignee_candidate(
        self,
        hw: Homework,
        assignee: AssigneeUserInfo,
        now_utc: datetime,
        hw_exercises: list[HomeworkExercise],
    ) -> ScannedCandidateTask | None:
        dl = assignee.deadline
        if not dl or not hw.id:
            return None

        hw_deadline_dt = self._normalize_deadline(dl)

        time_diff = (hw_deadline_dt - now_utc).total_seconds()
        if hw_deadline_dt < now_utc or time_diff > 3 * 86400:
            return None

        stages = calculate_matching_stages(hw_deadline_dt, now_utc)
        if not stages:
            return None

        uid = assignee.user_id
        submissions = self.homework_submission_repo.get_submissions_by_user(
            homework_id=hw.id, user_id=uid
        )
        evaluation = hw.evaluate_submissions(
            submissions,
            required_exercises=hw_exercises,
            deadline=hw_deadline_dt,
            reference_time=now_utc,
        )
        if evaluation.is_submitted:
            return None

        return ScannedCandidateTask(
            task_type=TaskType.HOMEWORK,
            task_id=hw.id,
            task_title=hw.title,
            user_id=uid,
            deadline=hw_deadline_dt,
            action_url="/dashboard/my-homeworks",
            stages=stages,
        )
