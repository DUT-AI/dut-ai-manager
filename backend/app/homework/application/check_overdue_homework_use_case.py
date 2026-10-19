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
from app.homework.domain.entity import SubmissionType
from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class CheckOverdueHomeworkUseCase:
    """Kiểm tra bài tập quá hạn và phát sự kiện HomeworkOverdueDetected qua EventBus."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.quiz_api = quiz_api
        self.user_repo = user_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.event_bus = event_bus

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        if not homework.id:
            return set()
        return self.homework_assignee_repo.get_assigned_user_ids(homework.id)

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

            coding_completed_uids = (
                await QuizSubmissionHelper.get_coding_completed_user_ids(
                    self.quiz_api, slug
                )
            )
            exercises = await QuizSubmissionHelper.get_lesson_exercises(
                self.quiz_api, slug
            )

            game_completed_uids = (
                await QuizSubmissionHelper.get_game_completed_user_ids(
                    self.quiz_api, slug
                )
            )

            has_coding = coding_completed_uids is not None
            has_game = game_completed_uids is not None

            # Nếu cả 2 đều là None (404/không tìm thấy trên Quiz API), bỏ qua
            if not has_coding and not has_game:
                continue

            assigned_uids = self._get_effective_assigned_user_ids(homework)
            if not assigned_uids:
                continue

            required_exercise_ids = set()
            if exercises:
                required_exercise_ids = {
                    str(ex.get("id"))
                    for ex in exercises
                    if isinstance(ex, dict) and ex.get("id")
                }

            # Xác định yêu cầu coding/game cho bài tập này
            if homework.requires_game and not homework.requires_coding:
                req_coding = False
                req_game = has_game
            elif homework.requires_coding and homework.requires_game:
                req_coding = has_coding
                req_game = has_game
            else:
                req_coding = has_coding
                req_game = has_game

            for user_id in assigned_uids:
                # 1. Kiểm tra mục Coding (nếu bài yêu cầu)
                coding_ok = True
                if req_coding:
                    db_coding = False
                    if (
                        hasattr(self.homework_submission_repo, "get_submitted_exercise_ids")
                        and required_exercise_ids
                    ):
                        submitted_ids = self.homework_submission_repo.get_submitted_exercise_ids(
                            homework.id, user_id, homework.deadline
                        )
                        db_coding = required_exercise_ids.issubset(submitted_ids)
                    elif hasattr(self.homework_submission_repo, "has_valid_submission"):
                        res = self.homework_submission_repo.has_valid_submission(
                            homework.id,
                            user_id,
                            SubmissionType.CODING,
                            homework.deadline,
                        )
                        db_coding = res is True
                    api_coding = user_id in (coding_completed_uids or set())
                    coding_ok = db_coding or api_coding

                # 2. Kiểm tra mục Game (nếu bài yêu cầu)
                game_ok = True
                if req_game:                   
                    res = self.homework_submission_repo.has_valid_submission(
                        homework.id, user_id, SubmissionType.GAME, homework.deadline
                    )
                    db_game = res is True
                    api_game = user_id in (game_completed_uids or set())
                    game_ok = db_game or api_game

                if coding_ok and game_ok:
                    continue

                uncompleted_labels = []
                if req_coding and not coding_ok:
                    uncompleted_labels.append("bài tập coding")

                if req_game and not game_ok:
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
