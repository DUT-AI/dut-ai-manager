"""
Homework Rescan Use Case — application layer.

Quét lại toàn bộ bài tập (cũ & mới) và phát event kiểm tra vi phạm quá hạn.
"""

from app.homework.application.check_overdue_homework_use_case import (
    CheckOverdueHomeworkUseCase,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.domain.event_bus import EventBus
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class RescanAllHomeworksUseCase:
    """Quét lại toàn bộ bài tập (cũ & mới), đồng bộ phân công bài cũ và phát event kiểm tra."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.checker = CheckOverdueHomeworkUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
            user_repo=user_repo,
            event_bus=event_bus,
        )
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api
        self.user_repo = user_repo

    async def execute(self, auto_sync_legacy: bool = True) -> int:
        """
        Quét lại toàn bộ các bài tập trong quá khứ có deadline <= hiện tại:
        1. Đồng bộ các bài tập cũ chưa có dữ liệu trong homework_assignees.
        2. Chạy kiểm tra vi phạm cho từng bài tập và phát sinh event tạo vi phạm chuẩn.
        """
        all_homeworks = self.homework_repo.get_all(limit=1000)
        now_date = get_current_utc7_time().date()
        past_homeworks = [
            hw for hw in all_homeworks if hw.deadline and hw.deadline.date() <= now_date
        ]

        total_violations_created = 0

        for hw in past_homeworks:
            if not hw.id:
                continue

            # Tự động đồng bộ bài tập cũ nếu thiếu assignees
            assigned_uids = self.checker._get_effective_assigned_user_ids(hw)
            if not assigned_uids and auto_sync_legacy:
                slug = QuizSubmissionHelper.extract_slug_from_entity(hw)
                legacy_uids: set[int] = set()

                if slug:
                    coding_uids = await QuizSubmissionHelper.get_coding_completed_user_ids(self.quiz_api, slug)
                    if coding_uids:
                        legacy_uids.update(coding_uids)
                    game_uids = await QuizSubmissionHelper.get_game_completed_user_ids(self.quiz_api, slug)
                    if game_uids:
                        legacy_uids.update(game_uids)

                if legacy_uids:
                    self.homework_repo.sync_assignees(
                        hw.id,
                        assignee_ids=list(legacy_uids),
                    )

            # Thực thi kiểm tra vi phạm cho bài tập này
            count = await self.checker.execute(target_date=hw.deadline.date())
            total_violations_created += count

        return total_violations_created
