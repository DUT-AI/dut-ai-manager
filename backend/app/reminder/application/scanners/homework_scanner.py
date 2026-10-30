"""
Homework Task Scanner.
Scans upcoming homeworks and filters out completed submissions.
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.reminder.application.scanners.base_scanner import (
    BaseTaskScanner,
    ScannedCandidateTask,
    calculate_matching_stages,
)
from app.reminder.domain.entity import TaskType


class HomeworkTaskScanner(BaseTaskScanner):
    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_submission_repo = homework_submission_repo

    def scan_pending_tasks(self, now: datetime) -> list[ScannedCandidateTask]:
        candidates: list[ScannedCandidateTask] = []
        all_homeworks = self.homework_repo.get_all(limit=200)

        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        now_utc = (
            now
            if now.tzinfo is not None
            else now.replace(tzinfo=vn_tz).astimezone(timezone.utc)
        )

        for hw in all_homeworks:
            if not hw.id or not hw.deadline:
                continue

            if isinstance(hw.deadline, datetime):
                if (
                    hw.deadline.hour == 0
                    and hw.deadline.minute == 0
                    and hw.deadline.second == 0
                ):
                    hw_deadline_dt = hw.deadline.replace(
                        hour=23,
                        minute=59,
                        second=59,
                        tzinfo=hw.deadline.tzinfo or vn_tz,
                    ).astimezone(timezone.utc)
                else:
                    hw_deadline_dt = (
                        hw.deadline
                        if hw.deadline.tzinfo is not None
                        else hw.deadline.replace(tzinfo=vn_tz).astimezone(timezone.utc)
                    )
            else:
                hw_deadline_dt = datetime.combine(
                    hw.deadline, datetime.min.time()
                ).replace(
                    hour=23, minute=59, second=59, tzinfo=vn_tz
                ).astimezone(timezone.utc)

            # Chỉ xét task có deadline trong tương lai và cách tối đa 3 ngày
            if (
                hw_deadline_dt < now_utc
                or (hw_deadline_dt - now_utc).total_seconds() > 3 * 86400
            ):
                continue

            stages = calculate_matching_stages(hw_deadline_dt, now_utc)
            if not stages:
                continue

            assignee_ids = self.homework_assignee_repo.get_assigned_user_ids(hw.id)
            if not assignee_ids:
                continue

            for uid in assignee_ids:
                # Kiểm tra xem user đã nộp bài chưa
                submissions = self.homework_submission_repo.get_submissions_by_user(
                    homework_id=hw.id, user_id=uid
                )
                if submissions:
                    continue  # Đã nộp bài, bỏ qua

                candidates.append(
                    ScannedCandidateTask(
                        task_type=TaskType.HOMEWORK,
                        task_id=hw.id,
                        task_title=hw.title,
                        user_id=uid,
                        deadline=hw_deadline_dt,
                        action_url="/dashboard/my-homeworks",
                        stages=stages,
                    )
                )

        return candidates
