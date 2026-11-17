from datetime import UTC, datetime

from app.homework.application.dtos import (
    CategorySubmissionStatus,
    ExerciseSummaryDTO,
    HomeworkSubmissionStatusResponse,
    StudentExerciseStatusDTO,
    StudentHomeworkDetailDTO,
    UserSubmissionInfo,
)
from app.homework.domain.entity import HomeworkSubmission
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.domain.value_objects import CompletionStatus
from app.user.infrastructure.repository import UserRepository


class GetHomeworkSubmissionStatusUseCase:
    """
    Trả về bảng tổng hợp trạng thái nộp bài (Coding & Game) cho màn hình quản trị.
    Ủy quyền 100% logic đánh giá cho Aggregate Root Homework.evaluate_submissions() (SSOT).
    """

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
        user_repo: UserRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo
        self.user_repo = user_repo

    async def execute(
        self, homework_id: int
    ) -> HomeworkSubmissionStatusResponse | None:
        homework = self.homework_repo.get_by_id(homework_id)
        if not homework or not homework.id:
            return None

        # 1. Thu thập dữ liệu từ DB (100% DB-first, không gọi live Quiz API)
        submissions = self.homework_submission_repo.get_submissions_by_homework(
            homework.id
        )
        assignees = self.homework_assignee_repo.get_assignees_with_user_info(
            homework.id
        )
        active_exercises = (
            self.homework_exercise_repo.get_active_by_homework(homework.id)
            if homework.requires_coding
            else []
        )

        # 2. Gom nhóm bài nộp theo user_id
        subs_by_user: dict[int, list[HomeworkSubmission]] = {}
        for sub in submissions:
            subs_by_user.setdefault(sub.user_id, []).append(sub)

        # 3. Đánh giá từng học viên bằng Aggregate Root SSOT Homework.evaluate_submissions()
        now = datetime.now(UTC)
        students: list[StudentHomeworkDetailDTO] = []
        total_completed = 0

        for assignee in assignees:
            user_subs = subs_by_user.get(assignee.user_id, [])
            evaluation = homework.evaluate_submissions(
                user_subs,
                required_exercises=active_exercises,
                deadline=assignee.deadline,
                reference_time=now,
            )

            if evaluation.completion_status == CompletionStatus.COMPLETED:
                total_completed += 1

            student_exercises = [
                StudentExerciseStatusDTO(
                    exercise_id=ex.exercise_id,
                    exercise_title=ex.title,
                    is_submitted=ex.is_submitted,
                    is_passed=ex.is_passed,
                    score=ex.best_score,
                    attempt_number=ex.attempt_count,
                    submitted_at=(
                        (ex.first_passed_at or ex.latest_submitted_at).isoformat()
                        if (ex.first_passed_at or ex.latest_submitted_at)
                        else None
                    ),
                    is_late=ex.is_late,
                )
                for ex in evaluation.coding_exercises
            ]

            students.append(
                StudentHomeworkDetailDTO(
                    user_id=assignee.user_id,
                    name=assignee.name,
                    avatar_url=assignee.avatar_url,
                    total_coding_required=evaluation.total_coding_required,
                    total_coding_completed=evaluation.total_coding_completed,
                    coding_status=evaluation.coding_status,
                    coding_is_late=evaluation.coding_is_late,
                    coding_exercises=student_exercises,
                    game_is_submitted=evaluation.game_submitted,
                    game_is_late=evaluation.game_is_late,
                    game_submitted_at=(
                        evaluation.game_first_passed_at.isoformat()
                        if evaluation.game_first_passed_at
                        else None
                    ),
                    game_score=evaluation.game_best_score,
                )
            )

        # 4. Tổng hợp tỷ lệ hoàn thành theo từng bài tập con chính thức
        coding_exercises = [
            ExerciseSummaryDTO(
                exercise_id=ex.exercise_id,
                title=ex.title,
                order_index=ex.order_index,
            )
            for ex in active_exercises
        ]
        self._calculate_exercise_completion_rates(
            coding_exercises, students, len(assignees)
        )

        # 5. Phân nhóm nộp bài Coding và Game
        coding_status, game_status = self._categorize_submissions(students)

        return HomeworkSubmissionStatusResponse(
            coding=coding_status,
            game=game_status,
            total_completed_count=total_completed,
            coding_exercises=coding_exercises,
            students=students,
        )

    def _calculate_exercise_completion_rates(
        self,
        exercises: list[ExerciseSummaryDTO],
        students: list[StudentHomeworkDetailDTO],
        total_assigned: int,
    ) -> None:
        for ex in exercises:
            ex.total_assigned = total_assigned
            ex.completed_count = sum(
                1
                for s in students
                if any(
                    ce.exercise_id == ex.exercise_id and ce.is_passed
                    for ce in s.coding_exercises
                )
            )
            ex.completion_rate = (
                round((ex.completed_count / total_assigned) * 100, 1)
                if total_assigned > 0
                else 0.0
            )

    def _categorize_submissions(
        self, students: list[StudentHomeworkDetailDTO]
    ) -> tuple[CategorySubmissionStatus, CategorySubmissionStatus]:
        coding_submitted: list[UserSubmissionInfo] = []
        coding_not_submitted: list[UserSubmissionInfo] = []
        game_submitted: list[UserSubmissionInfo] = []
        game_not_submitted: list[UserSubmissionInfo] = []

        for s in students:
            user_info = UserSubmissionInfo(
                user_id=s.user_id,
                name=s.name,
                avatar_url=s.avatar_url,
                is_late=s.coding_is_late if s.coding_status == "COMPLETED" else False,
                total_coding_required=s.total_coding_required,
                total_coding_completed=s.total_coding_completed,
                coding_status=s.coding_status,
                coding_exercises=s.coding_exercises,
            )

            if s.coding_status == "COMPLETED":
                coding_submitted.append(user_info)
            else:
                coding_not_submitted.append(user_info)

            if s.game_is_submitted:
                game_submitted.append(
                    UserSubmissionInfo(
                        user_id=s.user_id,
                        name=s.name,
                        avatar_url=s.avatar_url,
                        is_late=s.game_is_late,
                        submitted_at=s.game_submitted_at,
                    )
                )
            else:
                game_not_submitted.append(
                    UserSubmissionInfo(
                        user_id=s.user_id,
                        name=s.name,
                        avatar_url=s.avatar_url,
                        is_late=False,
                    )
                )

        return (
            CategorySubmissionStatus(
                submitted=coding_submitted, not_submitted=coding_not_submitted
            ),
            CategorySubmissionStatus(
                submitted=game_submitted, not_submitted=game_not_submitted
            ),
        )
