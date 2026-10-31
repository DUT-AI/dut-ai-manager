"""
Homework Checker Use Case — application layer.

Handles scheduled background checks (default: deadline = today - 2 days)
for overdue homework submissions by comparing assignees against submissions in database.
Publishes domain events (HomeworkOverdueDetected) for decoupled violation processing.
"""

from datetime import UTC, date, datetime, timedelta
from typing import cast
from zoneinfo import ZoneInfo

from loguru import logger

from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
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
from app.shared.domain.event_bus import DomainEvent, EventBus


class CheckOverdueHomeworkUseCase:
    """
    Kiểm tra bài tập quá hạn đối chiếu trực tiếp giữa Assignees và Submissions trong Database.
    Phát sự kiện HomeworkOverdueDetected qua EventBus để Violation Domain xử lý kỷ luật.
    """

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.event_bus = event_bus

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        if not homework.id:
            return set()
        return self.homework_assignee_repo.get_assigned_user_ids(homework.id)

    async def execute(self, target_date: date | None = None) -> int:
        """
        Quét tất cả các bài tập có deadline là target_date:
        - Mặc định khi chạy tự động (target_date is None): quét các bài phân công có deadline cách đây 2 ngày.
        - Khi truyền target_date cụ thể: quét chính xác các bài phân công có deadline ngày đó.
        1. Lấy danh sách phân công đến hạn (due_assignments) từ bảng homework_assignees.
        2. Đối soát bài nộp trong DB: chỉ chấp nhận bài nộp trước hoặc đúng deadline cá nhân (submitted_at <= assignee.deadline).
        3. Nếu CHƯA hoàn thành trước deadline -> Phát sự kiện HomeworkOverdueDetected lên EventBus.
        """
        if target_date is None:
            now = datetime.now(UTC)
            today_vn = now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
            target_date = today_vn - timedelta(days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS)

        due_assignments = self.homework_assignee_repo.get_by_deadline_date(
            target_date
        )
        if not due_assignments:
            logger.info(
                f"Không có bài tập nào có assignee deadline vào ngày {target_date}"
            )
            return 0

        # Nhóm assignments theo homework_id để cache required_exercise_ids
        hw_required_exercises: dict[int, set[str]] = {}
        for item in due_assignments:
            if item.homework_id not in hw_required_exercises:
                all_submissions = (
                    self.homework_submission_repo.get_submissions_by_homework(
                        item.homework_id
                    )
                )
                hw_required_exercises[item.homework_id] = {
                    str(s.exercise_id)
                    for s in all_submissions
                    if s.exercise_id
                    and str(s.submission_type).upper() == "CODING"
                    and not str(s.exercise_id).startswith("sync-legacy")
                }

        events_published_count = 0

        for assignment in due_assignments:
            user_id = assignment.user_id
            hw_id = assignment.homework_id
            assignee_deadline = assignment.deadline

            # Xác định yêu cầu coding/game cho bài tập
            req_coding = bool(assignment.requires_coding)
            req_game = bool(assignment.requires_game)

            # Nếu cả 2 đều chưa cấu hình bật rõ ràng, mặc định kiểm tra Coding
            if not req_coding and not req_game:
                req_coding = True

            required_exercise_ids = hw_required_exercises.get(hw_id, set())

            # 1. Kiểm tra Coding trong DB (chỉ chấp nhận submitted_at <= assignee_deadline)
            coding_ok = True
            if req_coding:
                if (
                    hasattr(
                        self.homework_submission_repo,
                        "get_submitted_exercise_ids",
                    )
                    and required_exercise_ids
                ):
                    submitted_ids = (
                        self.homework_submission_repo.get_submitted_exercise_ids(
                            hw_id, user_id, assignee_deadline
                        )
                    )
                    coding_ok = required_exercise_ids.issubset(submitted_ids)
                else:
                    coding_ok = (
                        self.homework_submission_repo.has_valid_submission(
                            hw_id,
                            user_id,
                            SubmissionType.CODING,
                            assignee_deadline,
                        )
                    )

            # 2. Kiểm tra Game trong DB (chỉ chấp nhận submitted_at <= assignee_deadline)
            game_ok = True
            if req_game:
                game_ok = self.homework_submission_repo.has_valid_submission(
                    hw_id,
                    user_id,
                    SubmissionType.GAME,
                    assignee_deadline,
                )

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
            reason_msg = (
                f"Chưa hoàn thành {items_str} ({assignment.homework_title})"
            )

            await self.event_bus.publish(
                cast(
                    DomainEvent,
                    HomeworkOverdueDetected(
                        user_id=user_id,
                        homework_id=hw_id,
                        homework_title=assignment.homework_title,
                        deadline_date=str(assignee_deadline.date()),
                        reason=reason_msg,
                        uncompleted_items=uncompleted_labels,
                    ),
                )
            )
            events_published_count += 1

        return events_published_count
