from app.homework.application.dtos import HomeworkResponse
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)


class GetUnsubmittedHomeworksForUserUseCase:
    """Use case lấy danh sách bài tập chưa nộp của một học viên cụ thể kiểm tra qua database."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo

    async def execute(self, user_id: int) -> list[HomeworkResponse]:
        # 1. Truy vấn bài tập được giao cho user trực tiếp từ Database thông qua SQL JOIN
        assigned_homeworks = self.homework_repo.get_all_assigned_to_user(
            user_id=user_id, deleted=False
        )

        if not assigned_homeworks:
            return []

        # 2. Get user submissions for these homeworks
        hw_ids = [hw.id for hw in assigned_homeworks if hw.id is not None]
        user_submissions = (
            self.homework_submission_repo.get_user_submissions_for_homeworks(
                homework_ids=hw_ids, user_id=user_id
            )
        )

        user_deadlines = self.homework_assignee_repo.get_user_deadlines_for_homeworks(
            homework_ids=hw_ids, user_id=user_id
        )

        required_exercises_map = (
            self.homework_submission_repo.get_required_exercise_ids_map(hw_ids)
        )

        submissions_by_hw: dict[int, list] = {}
        for sub in user_submissions:
            submissions_by_hw.setdefault(sub.homework_id, []).append(sub)

        # 3. Determine unsubmitted homeworks
        unsubmitted: list[HomeworkResponse] = []
        for hw in assigned_homeworks:
            assert hw.id is not None
            hw_subs = submissions_by_hw.get(hw.id, [])
            user_dl = user_deadlines.get(hw.id)
            hw_req_ex_ids = required_exercises_map.get(hw.id)
            eval_result = hw.evaluate_submissions(
                hw_subs, deadline=user_dl, required_exercise_ids=hw_req_ex_ids
            )
            if not eval_result.is_submitted:
                resp = HomeworkResponse.from_entity(hw, deadline=user_dl)
                resp.is_submitted = False
                resp.is_overdue = eval_result.is_overdue
                resp.has_coding = hw.requires_coding
                resp.coding_submitted = eval_result.coding_submitted
                resp.has_game = hw.requires_game
                resp.game_submitted = eval_result.game_submitted
                resp.uncompleted_items = eval_result.uncompleted_items
                resp.coding_status = eval_result.coding_status
                resp.total_coding_required = eval_result.total_coding_required
                resp.total_coding_completed = eval_result.total_coding_completed
                unsubmitted.append(resp)

        return unsubmitted
