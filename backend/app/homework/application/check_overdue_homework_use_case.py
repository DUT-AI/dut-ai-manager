from datetime import UTC, date, datetime, timedelta
from typing import cast
from zoneinfo import ZoneInfo

from loguru import logger

from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkExercise
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import (
    CompletionStatus,
    DueHomeworkAssignment,
    HomeworkOverdueDetected,
    SubmissionEvaluation,
)
from app.shared.domain.event_bus import DomainEvent, EventBus


class CheckOverdueHomeworkUseCase:
    """
    Kiểm tra bài tập quá hạn bằng Aggregate Root SSOT Homework.evaluate_submissions().
    Xét kỷ luật nghiêm ngặt theo tiêu chí `is_completed_on_time`:
    - Đã hoàn thành đúng hạn (kể cả sau đó có nộp lại cải thiện) -> KHÔNG phạt.
    - Hoàn thành sau hạn (`COMPLETED + LATE`) -> Phát vi phạm với lý do nộp trễ hạn rõ ràng.
    - Chưa hoàn thành (`NOT_STARTED / IN_PROGRESS`) -> Phát vi phạm liệt kê hạng mục còn thiếu.
    """

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo
        self.event_bus = event_bus

    def _evaluate_assignment(
        self,
        assignment: DueHomeworkAssignment,
        required_exercises: list[HomeworkExercise],
        homework_entity: HomeworkEntity | None = None,
    ) -> SubmissionEvaluation:
        user_id = assignment.user_id
        hw_id = assignment.homework_id
        assignee_deadline = assignment.deadline

        hw = homework_entity or self.homework_repo.get_by_id(hw_id)
        if not isinstance(hw, HomeworkEntity):
            hw = HomeworkEntity(
                id=hw_id,
                title=assignment.homework_title,
                requires_coding=assignment.requires_coding,
                requires_game=assignment.requires_game,
                slug=assignment.slug,
            )

        submissions = self.homework_submission_repo.get_submissions_by_user(
            hw_id, user_id
        )

        return hw.evaluate_submissions(
            submissions,
            required_exercises=required_exercises,
            deadline=assignee_deadline,
        )

    async def execute(self, target_date: date | None = None) -> int:
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

        hw_ids = sorted({item.homework_id for item in due_assignments})
        exercises_by_hw = self.homework_exercise_repo.get_active_by_homework_ids(hw_ids)
        hw_entities: dict[int, HomeworkEntity | None] = {
            hid: self.homework_repo.get_by_id(hid) for hid in hw_ids
        }

        events_published_count = 0
        for assignment in due_assignments:
            eval_result = self._evaluate_assignment(
                assignment=assignment,
                required_exercises=exercises_by_hw.get(assignment.homework_id, []),
                homework_entity=hw_entities.get(assignment.homework_id),
            )
            if eval_result.is_completed_on_time:
                continue

            if eval_result.completion_status == CompletionStatus.COMPLETED:
                reason_msg = f"Nộp bài tập trễ hạn ({assignment.homework_title})"
                uncompleted_labels = ["Nộp trễ hạn"]
            else:
                uncompleted_labels = eval_result.uncompleted_items
                items_str = " và ".join(uncompleted_labels)
                reason_msg = (
                    f"Chưa hoàn thành {items_str} ({assignment.homework_title})"
                )

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
