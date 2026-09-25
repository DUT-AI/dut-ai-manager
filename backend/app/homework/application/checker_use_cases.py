"""
Homework Checker Use Cases — application layer.

Handles daily background job (23:59) checking for overdue homework submissions
and publishing domain events (HomeworkOverdueDetected) for decoupled violation processing.
"""

from datetime import date
from typing import cast

from loguru import logger

from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class CheckOverdueHomeworkUseCase:
    """Kiểm tra bài tập quá hạn và phát sự kiện HomeworkOverdueDetected qua EventBus."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.event_bus = event_bus

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        assigned_uids: set[int] = set()
        user_ids = getattr(homework, "assignee_ids", None) or getattr(homework, "assigned_user_ids", None)
        if user_ids:
            assigned_uids.update(user_ids)

        team_ids = getattr(homework, "team_ids", None) or getattr(homework, "assigned_team_ids", None)
        if team_ids and self.team_repo:
            team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
            assigned_uids.update(team_user_ids)

        if not assigned_uids and homework.id and hasattr(self.homework_repo, "get_assigned_user_ids"):
            repo_uids = self.homework_repo.get_assigned_user_ids(homework.id)
            if repo_uids:
                assigned_uids.update(repo_uids)

        return assigned_uids

    async def execute(self, target_date: date | None = None) -> int:
        """
        Quét tất cả các bài tập có deadline là target_date (mặc định là hôm nay):
        1. Lấy danh sách thành viên được phân công.
        2. Kiểm tra xem họ có hoàn thành Coding và Game (nếu có) trên Quiz API không.
        3. Nếu CHƯA hoàn thành -> Phát sự kiện HomeworkOverdueDetected lên EventBus.
        """
        if target_date is None:
            now = get_current_utc7_time()
            target_date = now.date()

        due_homeworks = self.homework_repo.get_by_deadline_date(target_date)
        if not due_homeworks:
            logger.info(f"Không có bài tập nào có deadline vào ngày {target_date}")
            return 0

        events_published_count = 0

        for homework in due_homeworks:
            if not homework.id:
                continue

            slug = QuizSubmissionHelper.extract_slug_from_entity(homework)
            if not slug:
                logger.warning(
                    f"Bài tập id={homework.id} '{homework.title}' không có slug/link hợp lệ để gọi Quiz API. Bỏ qua."
                )
                continue

            hw_type = QuizSubmissionHelper.detect_homework_type(homework.link, homework.slug)

            coding_completed_uids = None
            if hw_type in ("coding", "both"):
                coding_completed_uids = await QuizSubmissionHelper.get_coding_completed_user_ids(self.quiz_api, slug)

            game_completed_uids = None
            if hw_type in ("game", "both"):
                game_completed_uids = await QuizSubmissionHelper.get_game_completed_user_ids(self.quiz_api, slug)

            assigned_uids = self._get_effective_assigned_user_ids(homework)
            if not assigned_uids:
                continue

            for user_id in assigned_uids:
                coding_set = coding_completed_uids or set()
                game_set = game_completed_uids or set()

                if QuizSubmissionHelper.is_user_submitted(user_id, coding_set, game_set):
                    continue

                uncompleted_labels = []
                has_coding = len(coding_set) > 0
                has_game = len(game_set) > 0

                if (has_coding or not has_game) and user_id not in coding_set:
                    uncompleted_labels.append("bài tập coding")

                if has_game and user_id not in game_set:
                    uncompleted_labels.append("trắc nghiệm game")

                if not uncompleted_labels:
                    continue

                items_str = " và ".join(uncompleted_labels)
                reason_msg = f"Chưa hoàn thành {items_str} ({homework.title})"

                await self.event_bus.publish(
                    cast(
                        DomainEvent,
                        HomeworkOverdueDetected(
                            user_id=user_id,
                            homework_id=homework.id,
                            homework_title=homework.title,
                            deadline_date=str(homework.deadline.date()),
                            reason=reason_msg,
                            uncompleted_items=uncompleted_labels,
                        ),
                    )
                )
                events_published_count += 1

        return events_published_count


class RescanAllHomeworksUseCase:
    """Quét lại toàn bộ bài tập (cũ & mới), đồng bộ team phân công bài cũ và phát event kiểm tra."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
        team_repo: TeamRepository | None = None,
        event_bus: type[EventBus] = EventBus,
    ):
        self.checker = CheckOverdueHomeworkUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
            user_repo=user_repo,
            team_repo=team_repo,
            event_bus=event_bus,
        )
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api
        self.team_repo = team_repo
        self.user_repo = user_repo

    async def execute(self, auto_sync_legacy: bool = True) -> int:
        """
        Quét lại toàn bộ các bài tập trong quá khứ có deadline <= hiện tại:
        1. Đồng bộ các bài tập cũ chưa có dữ liệu trong homework_assignees/homework_teams.
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

            # Tự động đồng bộ bài tập cũ nếu thiếu assignees/teams
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
                    if hasattr(self.homework_repo, "sync_assignees_and_teams"):
                        self.homework_repo.sync_assignees_and_teams(
                            hw.id,
                            assignee_ids=list(legacy_uids),
                            team_ids=None,
                        )

            # Thực thi kiểm tra vi phạm cho bài tập này
            count = await self.checker.execute(target_date=hw.deadline.date())
            total_violations_created += count

        return total_violations_created
