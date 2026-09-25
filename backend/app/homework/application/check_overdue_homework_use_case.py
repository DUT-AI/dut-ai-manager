"""
Homework Checker Use Case — application layer.

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
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class CheckOverdueHomeworkUseCase:
    """Kiểm tra bài tập quá hạn và phát sự kiện HomeworkOverdueDetected qua EventBus."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.quiz_api = quiz_api
        self.user_repo = user_repo
        self.event_bus = event_bus

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        assigned_uids = set(homework.assignee_ids or [])
        if not assigned_uids and homework.id:
            repo_uids = self.homework_repo.get_assigned_user_ids(homework.id)
            if repo_uids:
                assigned_uids.update(repo_uids)
        return assigned_uids

    async def execute(self, target_date: date | None = None) -> int:
        """
        Quét tất cả các bài tập có deadline là target_date (mặc định là hôm nay):
        1. Lấy danh sách thành viên được phân công (assignee_ids).
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

            # Nếu cả 2 đều là None (404/không tìm thấy trên Quiz API), bỏ qua
            if coding_completed_uids is None and game_completed_uids is None:
                continue

            assigned_uids = self._get_effective_assigned_user_ids(homework)
            if not assigned_uids:
                continue

            for user_id in assigned_uids:
                if QuizSubmissionHelper.is_user_submitted(user_id, coding_completed_uids, game_completed_uids):
                    continue

                uncompleted_labels = []
                has_coding = coding_completed_uids is not None
                has_game = game_completed_uids is not None

                if has_coding and user_id not in (coding_completed_uids or set()):
                    uncompleted_labels.append("bài tập coding")

                if has_game and user_id not in (game_completed_uids or set()):
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
