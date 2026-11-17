from datetime import UTC, datetime

from loguru import logger

from app.homework.application.dtos import SyncHomeworkResult, SyncMyHomeworksResult
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.application.sync_homework_use_case import (
    SyncHomeworkFromQuizUseCase,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import CompletionStatus

MAX_HOMEWORKS_PER_USER_SYNC = 10


class SyncMyUnsubmittedHomeworksUseCase:
    """
    Use case cho phép học viên chủ động đồng bộ nhanh các bài tập chưa hoàn thành của chính mình từ Quiz API.
    Giới hạn tối đa 10 bài mỗi lượt (ưu tiên bài mới nhất) và fail-safe từng bài độc lập.
    """

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
        sync_homework_uc: SyncHomeworkFromQuizUseCase,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo
        self.sync_homework_uc = sync_homework_uc

    async def execute(self, user_id: int) -> SyncMyHomeworksResult:
        assigned = self.homework_repo.get_all_assigned_to_user(
            user_id=user_id, deleted=False
        )
        if not assigned:
            return SyncMyHomeworksResult()

        now = datetime.now(UTC)
        hw_ids = [hw.id for hw in assigned if hw.id is not None]
        user_submissions = (
            self.homework_submission_repo.get_user_submissions_for_homeworks(
                homework_ids=hw_ids, user_id=user_id
            )
        )
        user_deadlines = self.homework_assignee_repo.get_user_deadlines_for_homeworks(
            hw_ids, user_id
        )
        exercises_by_hw = self.homework_exercise_repo.get_active_by_homework_ids(hw_ids)

        subs_by_hw: dict[int, list] = {}
        for sub in user_submissions:
            subs_by_hw.setdefault(sub.homework_id, []).append(sub)

        # Lọc các bài chưa hoàn thành và có slug hợp lệ (giới hạn tối đa 10 bài mới nhất)
        candidates = []
        for hw in assigned:
            if not hw.id:
                continue
            if not QuizSubmissionHelper.extract_slug_from_entity(hw):
                continue
            eval_result = hw.evaluate_submissions(
                subs_by_hw.get(hw.id, []),
                required_exercises=exercises_by_hw.get(hw.id, []),
                deadline=user_deadlines.get(hw.id),
                reference_time=now,
            )
            if eval_result.completion_status != CompletionStatus.COMPLETED:
                candidates.append(hw)
            if len(candidates) >= MAX_HOMEWORKS_PER_USER_SYNC:
                break

        results: list[SyncHomeworkResult] = []
        failed_ids: list[int] = []

        for hw in candidates:
            assert hw.id is not None
            try:
                res = await self.sync_homework_uc.execute(hw.id)
                results.append(res)
            except Exception as exc:
                logger.warning(
                    f"[SyncMyHomeworks] Đồng bộ thất bại homework_id={hw.id} cho user_id={user_id}: {exc}"
                )
                failed_ids.append(hw.id)

        return SyncMyHomeworksResult(
            total_checked=len(candidates),
            synced_count=len(results),
            failed_count=len(failed_ids),
            results=results,
            failed_homework_ids=failed_ids,
        )
