from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from zoneinfo import ZoneInfo

from loguru import logger

from app.homework.application.homework_exercise_resolver import (
    HomeworkExerciseResolver,
)
from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import SubmissionType
from app.homework.domain.value_objects import (
    DueHomeworkAssignment,
    HomeworkOverdueDetected,
)
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.shared.domain.event_bus import DomainEvent, EventBus


class CheckOverdueHomeworkUseCase:
    """
    Kiểm tra bài tập quá hạn đối chiếu Assignees và Submissions trong Database.
    Phát sự kiện HomeworkOverdueDetected qua EventBus để kỷ luật.
    """

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        exercise_resolver: HomeworkExerciseResolver,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.exercise_resolver = exercise_resolver
        self.event_bus = event_bus

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        if not homework.id:
            return set()
        return self.homework_assignee_repo.get_assigned_user_ids(homework.id)

    def _evaluate_assignment(
        self,
        assignment: DueHomeworkAssignment,
        required_exercise_ids: set[str],
        homework_entity: HomeworkEntity | None = None,
    ) -> list[str]:
        """Đánh giá assignment và trả về danh sách các phần mục chưa hoàn thành."""
        user_id = assignment.user_id
        hw_id = assignment.homework_id
        assignee_deadline = assignment.deadline

        # 1. Ưu tiên đánh giá qua Aggregate Root Homework.evaluate_submissions nếu có bài nộp
        hw = homework_entity or self.homework_repo.get_by_id(hw_id)
        if not hw:
            hw = HomeworkEntity(
                id=hw_id,
                title=assignment.homework_title,
                requires_coding=assignment.requires_coding,
                requires_game=assignment.requires_game,
                slug=assignment.slug,
            )

        submissions: list[Any] = []
        user_subs = self.homework_submission_repo.get_submissions_by_user(
            hw_id, user_id
        )
        if isinstance(user_subs, list):
            submissions = user_subs

        if submissions:
            eval_result = hw.evaluate_submissions(
                submissions,
                deadline=assignee_deadline,
                required_exercise_ids=required_exercise_ids,
            )
            if eval_result.is_submitted:
                return []
            return eval_result.uncompleted_items

        # 2. Fallback kiểm tra từng phần mục qua các truy vấn repository chuyên biệt
        req_coding = bool(assignment.requires_coding)
        req_game = bool(assignment.requires_game)
        if not req_coding and not req_game:
            req_coding = True

        uncompleted: list[str] = []
        if req_coding and not self._is_coding_completed(
            hw_id, user_id, assignee_deadline, required_exercise_ids
        ):
            uncompleted.append("bài tập coding")
        if req_game and not self._is_game_completed(hw_id, user_id, assignee_deadline):
            uncompleted.append("trắc nghiệm game")
        return uncompleted

    def _is_coding_completed(
        self,
        hw_id: int,
        user_id: int,
        assignee_deadline: datetime,
        required_exercise_ids: set[str],
    ) -> bool:
        if required_exercise_ids:
            submitted_ids = self.homework_submission_repo.get_submitted_exercise_ids(
                hw_id, user_id, assignee_deadline
            )
            return required_exercise_ids.issubset(submitted_ids)
        return self.homework_submission_repo.has_valid_submission(
            hw_id,
            user_id,
            SubmissionType.CODING,
            assignee_deadline,
        )

    def _is_game_completed(
        self,
        hw_id: int,
        user_id: int,
        assignee_deadline: datetime,
    ) -> bool:
        return self.homework_submission_repo.has_valid_submission(
            hw_id,
            user_id,
            SubmissionType.GAME,
            assignee_deadline,
        )

    async def execute(self, target_date: date | None = None) -> int:
        """
        Quét tất cả các bài tập có deadline là target_date:
        - Mặc định: quét các bài phân công có deadline cách đây 2 ngày.
        - Khi truyền target_date: quét chính xác các bài có deadline ngày đó.
        """
        if target_date is None:
            now = datetime.now(UTC)
            today_vn = now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
            target_date = today_vn - timedelta(days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS)

        due_assignments = self.homework_assignee_repo.get_by_deadline_date(target_date)
        if not due_assignments:
            logger.info(
                f"Không có bài tập nào có assignee deadline vào ngày {target_date}"
            )
            return 0

        # Phân giải và cache danh sách bài tập con qua HomeworkExerciseResolver (SSOT)
        hw_required_exercises: dict[int, set[str]] = {}
        hw_entities: dict[int, HomeworkEntity | None] = {}
        for item in due_assignments:
            if item.homework_id not in hw_required_exercises:
                hw_required_exercises[item.homework_id] = (
                    await self.exercise_resolver.resolve_required_exercise_ids(
                        item.homework_id, item.slug
                    )
                )
                hw_entities[item.homework_id] = self.homework_repo.get_by_id(
                    item.homework_id
                )

        events_published_count = 0
        for assignment in due_assignments:
            uncompleted_labels = self._evaluate_assignment(
                assignment=assignment,
                required_exercise_ids=hw_required_exercises.get(
                    assignment.homework_id, set()
                ),
                homework_entity=hw_entities.get(assignment.homework_id),
            )
            if not uncompleted_labels:
                continue

            items_str = " và ".join(uncompleted_labels)
            reason_msg = f"Chưa hoàn thành {items_str} ({assignment.homework_title})"

            await self.event_bus.publish(
                cast(
                    DomainEvent,
                    HomeworkOverdueDetected(
                        user_id=assignment.user_id,
                        homework_id=assignment.homework_id,
                        homework_title=assignment.homework_title,
                        deadline_date=str(assignment.deadline.date()),
                        reason=reason_msg,
                        uncompleted_items=uncompleted_labels,
                        deadline=assignment.deadline,
                    ),
                )
            )
            events_published_count += 1

        return events_published_count
