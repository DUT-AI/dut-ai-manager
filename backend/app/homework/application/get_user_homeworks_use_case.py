from datetime import UTC, datetime
from typing import Literal

from app.homework.application.dtos import (
    HomeworkResponse,
    MyHomeworksPageResponse,
    MyHomeworksStats,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import CompletionStatus, TimelinessStatus

HomeworkFilterStatus = Literal["all", "uncompleted", "completed", "overdue"]


class GetUserHomeworksUseCase:
    """
    Use case lấy danh sách bài tập được giao cho học viên kèm thống kê tổng (100% bài được giao),
    lọc trạng thái, tìm kiếm tên bài tập và phân trang hoàn toàn phía máy chủ (DB-First SSOT).
    """

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo

    async def execute(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: HomeworkFilterStatus = "all",
        search: str | None = None,
    ) -> tuple[MyHomeworksPageResponse, int]:
        # 1. Lấy toàn bộ bài tập được giao cho học viên để tính stats chính xác 100%
        all_assigned = self.homework_repo.get_all_assigned_to_user(
            user_id=user_id,
            deleted=False,
        )
        if not all_assigned:
            return MyHomeworksPageResponse(items=[], stats=MyHomeworksStats()), 0

        now = datetime.now(UTC)
        all_hw_ids = [hw.id for hw in all_assigned if hw.id is not None]

        # 2. Batch-load submissions, personal deadlines, and official active exercises (3 SQL queries)
        user_submissions = (
            self.homework_submission_repo.get_user_submissions_for_homeworks(
                homework_ids=all_hw_ids, user_id=user_id
            )
        )
        user_deadlines = self.homework_assignee_repo.get_user_deadlines_for_homeworks(
            all_hw_ids, user_id
        )
        exercises_by_hw = self.homework_exercise_repo.get_active_by_homework_ids(
            all_hw_ids
        )

        submissions_by_hw: dict[int, list] = {}
        for sub in user_submissions:
            submissions_by_hw.setdefault(sub.homework_id, []).append(sub)

        # 3. Đánh giá 100% bài tập qua Aggregate Root SSOT và tổng hợp stats
        evaluated_responses = [
            HomeworkResponse.from_evaluation(
                hw,
                hw.evaluate_submissions(
                    submissions_by_hw.get(hw.id, []),
                    required_exercises=exercises_by_hw.get(hw.id, []),
                    deadline=user_deadlines.get(hw.id),
                    reference_time=now,
                ),
                deadline=user_deadlines.get(hw.id),
            )
            for hw in all_assigned
            if hw.id is not None
        ]
        stats = self._compute_stats(evaluated_responses)

        # 4. Áp dụng lọc trạng thái, tìm kiếm và phân trang
        filtered = self._filter_responses(evaluated_responses, status, search)
        total_filtered = len(filtered)
        safe_page = max(1, page)
        safe_size = max(1, page_size)
        offset = (safe_page - 1) * safe_size
        paged_items = filtered[offset : offset + safe_size]

        return MyHomeworksPageResponse(items=paged_items, stats=stats), total_filtered

    @staticmethod
    def _compute_stats(responses: list[HomeworkResponse]) -> MyHomeworksStats:
        completed = [
            r for r in responses if r.completion_status == CompletionStatus.COMPLETED
        ]
        uncompleted = [
            r for r in responses if r.completion_status != CompletionStatus.COMPLETED
        ]
        return MyHomeworksStats(
            total=len(responses),
            completed=len(completed),
            completed_on_time=sum(
                1 for r in completed if r.timeliness_status != TimelinessStatus.LATE
            ),
            completed_late=sum(
                1 for r in completed if r.timeliness_status == TimelinessStatus.LATE
            ),
            uncompleted=len(uncompleted),
            overdue=sum(
                1
                for r in uncompleted
                if r.timeliness_status == TimelinessStatus.OVERDUE
            ),
        )

    @staticmethod
    def _filter_responses(
        responses: list[HomeworkResponse],
        status: HomeworkFilterStatus,
        search: str | None,
    ) -> list[HomeworkResponse]:
        search_term = search.strip().lower() if search and search.strip() else None
        result: list[HomeworkResponse] = []
        for resp in responses:
            if search_term and search_term not in resp.title.lower():
                continue
            if not GetUserHomeworksUseCase._matches_status(resp, status):
                continue
            result.append(resp)
        return result

    @staticmethod
    def _matches_status(
        resp: HomeworkResponse, status: HomeworkFilterStatus
    ) -> bool:
        if status == "uncompleted":
            return resp.completion_status != CompletionStatus.COMPLETED
        if status == "completed":
            return resp.completion_status == CompletionStatus.COMPLETED
        if status == "overdue":
            return resp.timeliness_status == TimelinessStatus.OVERDUE
        return True
