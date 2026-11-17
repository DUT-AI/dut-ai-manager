"""
Homework Rescan Use Case — application layer.

Quét lại toàn bộ bài tập (cũ & mới) và phát event kiểm tra vi phạm quá hạn.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.homework.application.check_overdue_homework_use_case import (
    CheckOverdueHomeworkUseCase,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import EventBus
from app.user.infrastructure.repository import UserRepository


class RescanAllHomeworksUseCase:
    """Quét lại toàn bộ bài tập (cũ & mới), đồng bộ phân công bài cũ và phát event kiểm tra."""

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
        user_repo: UserRepository,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        quiz_api: QuizApiClient,
        event_bus: type[EventBus] = EventBus,
    ):
        self.checker = CheckOverdueHomeworkUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            homework_exercise_repo=homework_exercise_repo,
            event_bus=event_bus,
        )
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_exercise_repo = homework_exercise_repo
        self.user_repo = user_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.quiz_api = quiz_api

    async def execute(self, auto_sync_legacy: bool = True) -> int:
        all_homeworks = self.homework_repo.get_all(limit=1000)
        now_date = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()

        if auto_sync_legacy:
            for hw in all_homeworks:
                if not hw.id:
                    continue

                assigned_uids = self.homework_assignee_repo.get_assigned_user_ids(hw.id)
                if not assigned_uids:
                    slug = QuizSubmissionHelper.extract_slug_from_entity(hw)
                    legacy_uids: set[int] = set()

                    if slug:
                        coding_uids = (
                            await QuizSubmissionHelper.get_coding_completed_user_ids(
                                self.quiz_api, slug
                            )
                        )
                        if coding_uids:
                            legacy_uids.update(coding_uids)
                        game_uids = (
                            await QuizSubmissionHelper.get_game_completed_user_ids(
                                self.quiz_api, slug
                            )
                        )
                        if game_uids:
                            legacy_uids.update(game_uids)

                    if legacy_uids:
                        self.homework_assignee_repo.sync_assignees(
                            hw.id,
                            assignee_ids=list(legacy_uids),
                            default_deadline=datetime.now(UTC),
                        )

        past_dates = self.homework_assignee_repo.get_distinct_past_deadline_dates(
            before_date=now_date
        )

        total_violations_created = 0
        for target_date in past_dates:
            count = await self.checker.execute(target_date=target_date)
            total_violations_created += count

        return total_violations_created
