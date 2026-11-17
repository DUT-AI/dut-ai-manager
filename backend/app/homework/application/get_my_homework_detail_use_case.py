from datetime import UTC, datetime

from app.homework.application.dtos import (
    HomeworkResponse,
    HomeworkSubmissionDetailResponse,
    MyHomeworkDetailResponse,
    MyHomeworkExerciseStatusDTO,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)


class GetMyHomeworkDetailUseCase:
    """
    Use case lấy chi tiết bài tập cá nhân của học viên đang đăng nhập:
    - Trả về đúng hạn nộp cá nhân (từ homework_assignees)
    - Đánh giá trạng thái 2 chiều từ Aggregate Root SSOT
    - Trả về danh sách bài tập con bắt buộc chính thức kèm tiến độ từng bài và toàn bộ lịch sử nộp bài.
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
        self, homework_id: int, user_id: int
    ) -> MyHomeworkDetailResponse | None:
        homework = self.homework_repo.get_by_id(homework_id)
        if not homework or not homework.id:
            return None

        # Xác minh học viên được giao bài tập này và lấy đúng hạn nộp cá nhân
        user_deadline = self.homework_assignee_repo.get_user_deadline(
            homework.id, user_id
        )
        if user_deadline is None:
            return None

        active_exercises = self.homework_exercise_repo.get_active_by_homework(
            homework.id
        )
        submissions = self.homework_submission_repo.get_submissions_by_user(
            homework.id, user_id
        )

        now = datetime.now(UTC)
        evaluation = homework.evaluate_submissions(
            submissions,
            required_exercises=active_exercises,
            deadline=user_deadline,
            reference_time=now,
        )

        exercise_dtos = [
            MyHomeworkExerciseStatusDTO(
                exercise_id=ex.exercise_id,
                title=ex.title,
                order_index=ex.order_index,
                is_submitted=ex.is_submitted,
                is_passed=ex.is_passed,
                first_passed_at=ex.first_passed_at,
                latest_submitted_at=ex.latest_submitted_at,
                best_score=ex.best_score,
                attempt_count=ex.attempt_count,
                is_late=ex.is_late,
            )
            for ex in evaluation.coding_exercises
        ]

        submission_dtos = [
            HomeworkSubmissionDetailResponse.model_validate(sub) for sub in submissions
        ]

        return MyHomeworkDetailResponse(
            homework=HomeworkResponse.from_evaluation(
                homework, evaluation, deadline=user_deadline
            ),
            coding_exercises=exercise_dtos,
            submissions=submission_dtos,
        )
