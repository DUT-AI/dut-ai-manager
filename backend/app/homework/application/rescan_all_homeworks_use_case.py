"""
Homework Rescan Use Case — application layer.

Scans all past homework deadline dates and emits overdue violation events.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.homework.application.check_overdue_homework_use_case import (
    CheckOverdueHomeworkUseCase,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.shared.domain.event_bus import EventBus


class RescanAllHomeworksUseCase:
    """Rescans past homework deadlines and triggers overdue violation checks."""

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        event_bus: type[EventBus] = EventBus,
    ):
        self.checker = CheckOverdueHomeworkUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            homework_exercise_repo=homework_exercise_repo,
            event_bus=event_bus,
        )
        self.homework_assignee_repo = homework_assignee_repo

    async def execute(self) -> int:
        now_date = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
        past_dates = self.homework_assignee_repo.get_distinct_past_deadline_dates(
            before_date=now_date
        )

        total_violations_created = 0
        for target_date in past_dates:
            count = await self.checker.execute(target_date=target_date)
            total_violations_created += count

        return total_violations_created
