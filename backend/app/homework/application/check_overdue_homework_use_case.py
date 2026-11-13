from datetime import UTC, date, datetime, timedelta
from typing import cast
from zoneinfo import ZoneInfo

from loguru import logger

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
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import DomainEvent, EventBus

HOMEWORK_VIOLATION_CHECK_DELAY_DAYS = 2


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
        quiz_api: QuizApiClient,
        event_bus: type[EventBus] = EventBus,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.quiz_api = quiz_api
        self.event_bus = event_bus

    def _get_effective_assigned_user_ids(self, homework: HomeworkEntity) -> set[int]:
        if not homework.id:
            return set()
        return self.homework_assignee_repo.get_assigned_user_ids(homework.id)

    async def _resolve_required_exercises(
        self, homework_id: int, slug: str | None
    ) -> set[str]:
        """Lấy danh sách mã bài tập con từ Quiz API hoặc fallback submissions."""
        if not slug:
            hw = self.homework_repo.get_by_id(homework_id)
            slug = hw.slug if hw else None

        quiz_exercises = None
        if slug:
            try:
                quiz_exercises = await self.quiz_api.get_lesson_exercises(slug)
            except Exception as e:
                logger.warning(
                    f"[CheckOverdue] Lỗi lấy bài tập từ Quiz API (slug='{slug}'): {e}"
                )

        if quiz_exercises:
            return {
                str(ex["id"])
                for ex in quiz_exercises
                if isinstance(ex, dict) and "id" in ex
            }

        all_submissions = self.homework_submission_repo.get_submissions_by_homework(
            homework_id
        )
        return {
            str(s.exercise_id)
            for s in all_submissions
            if s.exercise_id
            and str(s.submission_type).upper() == "CODING"
            and not str(s.exercise_id).startswith("sync-legacy")
        }

    def _is_coding_completed(
        self,
        homework_id: int,
        user_id: int,
        deadline: datetime,
        required_exercise_ids: set[str],
    ) -> bool:
        """Kiểm tra xem học sinh đã hoàn thành đủ các bài coding trước deadline chưa."""
        if (
            hasattr(self.homework_submission_repo, "get_submitted_exercise_ids")
            and required_exercise_ids
        ):
            submitted_ids = self.homework_submission_repo.get_submitted_exercise_ids(
                homework_id, user_id, deadline
            )
            return required_exercise_ids.issubset(submitted_ids)

        return self.homework_submission_repo.has_valid_submission(
            homework_id,
            user_id,
            SubmissionType.CODING,
            deadline,
        )

    def _evaluate_assignment(
        self,
        assignment: DueHomeworkAssignment,
        required_exercise_ids: set[str],
    ) -> list[str]:
        """Đánh giá assignment và trả về danh sách các phần mục chưa hoàn thành."""
        user_id = assignment.user_id
        hw_id = assignment.homework_id
        assignee_deadline = assignment.deadline

        req_coding = bool(assignment.requires_coding)
        req_game = bool(assignment.requires_game)
        if not req_coding and not req_game:
            req_coding = True

        coding_ok = True
        if req_coding:
            coding_ok = self._is_coding_completed(
                hw_id, user_id, assignee_deadline, required_exercise_ids
            )

        game_ok = True
        if req_game:
            game_ok = self.homework_submission_repo.has_valid_submission(
                hw_id,
                user_id,
                SubmissionType.GAME,
                assignee_deadline,
            )

        uncompleted: list[str] = []
        if req_coding and not coding_ok:
            uncompleted.append("bài tập coding")
        if req_game and not game_ok:
            uncompleted.append("trắc nghiệm game")
        return uncompleted

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

        # Nhóm assignments theo homework_id để cache required_exercise_ids
        hw_required_exercises: dict[int, set[str]] = {}
        for item in due_assignments:
            if item.homework_id not in hw_required_exercises:
                hw_required_exercises[
                    item.homework_id
                ] = await self._resolve_required_exercises(item.homework_id, item.slug)

        events_published_count = 0
        for assignment in due_assignments:
            uncompleted_labels = self._evaluate_assignment(
                assignment, hw_required_exercises.get(assignment.homework_id, set())
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
