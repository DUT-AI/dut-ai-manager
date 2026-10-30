from datetime import UTC, datetime
from typing import Any

from app.homework.application.dtos import (
    CategorySubmissionStatus,
    ExerciseSummaryDTO,
    HomeworkSubmissionStatusResponse,
    StudentExerciseStatusDTO,
    StudentHomeworkDetailDTO,
    UserSubmissionInfo,
)
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.homework_assignee_repository import (
    AssigneeUserInfo,
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import (
    HomeworkRepository,
)
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.user.infrastructure.repository import UserRepository


class GetHomeworkSubmissionStatusUseCase:
    """Return submitted/not_submitted separated by Coding and Game, with per-exercise breakdown."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        user_repo: UserRepository,
        quiz_api: QuizApiClient,
        permission_repo: PermissionRequestRepository | None = None,
    ):
        self.homework_repo = homework_repo
        self.homework_submission_repo = homework_submission_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.user_repo = user_repo
        self.quiz_api = quiz_api
        self.permission_repo = permission_repo

    async def execute(
        self, homework_id: int
    ) -> HomeworkSubmissionStatusResponse | None:
        """Orchestrator: Điều phối thu thập dữ liệu và tổng hợp báo cáo nộp bài của học sinh."""
        homework = self.homework_repo.get_by_id(homework_id)
        if not homework or not homework.id:
            return None

        # 1. Thu thập dữ liệu từ các Repository
        submissions = self.homework_submission_repo.get_submissions_by_homework(
            homework.id
        )
        assignees = self.homework_assignee_repo.get_assignees_with_user_info(
            homework.id
        )
        postpone_map = self._get_postpone_map(
            homework.id, [a.user_id for a in assignees]
        )

        # 2. Lập bản đồ bài nộp thông qua Aggregate Root Homework
        db_exercise_map, db_coding_general_map, db_game_map = (
            homework.index_submissions(submissions)
        )

        # 3. Trích xuất danh mục các bài tập con
        coding_exercises = self._extract_coding_exercises(db_exercise_map, submissions)

        # 4. Đánh giá trạng thái từng học viên
        now = datetime.now(UTC)
        students = [
            self._evaluate_student(
                assignee=assignee,
                homework=homework,
                coding_exercises=coding_exercises,
                db_exercise_map=db_exercise_map,
                db_coding_general_map=db_coding_general_map,
                db_game_map=db_game_map,
                postpone_req=postpone_map.get((assignee.user_id, homework.id)),
                now=now,
            )
            for assignee in assignees
        ]

        # 5. Tính tỷ lệ hoàn thành theo từng bài tập con
        self._calculate_exercise_completion_rates(
            coding_exercises, students, len(assignees)
        )

        # 6. Phân nhóm nộp bài Coding và Game
        coding_status, game_status = self._categorize_submissions(students)

        return HomeworkSubmissionStatusResponse(
            coding=coding_status,
            game=game_status,
            coding_exercises=coding_exercises,
            students=students,
        )

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _get_postpone_map(
        self, homework_id: int, user_ids: list[int]
    ) -> dict[tuple[int, int], PermissionRequest]:
        """Lấy bản đồ đơn xin hoãn nộp bài theo (user_id, homework_id)."""
        if not self.permission_repo or not user_ids:
            return {}
        requests = self.permission_repo.get_postpone_requests_for_homeworks(
            homework_ids=[homework_id], user_ids=user_ids
        )
        return {(r.created_by, r.homework_id): r for r in requests}

    def _extract_coding_exercises(
        self, db_exercise_map: dict[tuple[int, str], Any], submissions: list[Any]
    ) -> list[ExerciseSummaryDTO]:
        """Trích xuất danh mục các bài tập con từ các bản ghi nộp bài đã lưu."""
        if not db_exercise_map:
            return []
        known_ex_ids = {k[1] for k in db_exercise_map.keys()}
        exercises: list[ExerciseSummaryDTO] = []
        for idx, ex_id in enumerate(sorted(known_ex_ids)):
            title = f"Bài tập {idx + 1}"
            for sub in submissions:
                if sub.exercise_id == ex_id and sub.exercise_title:
                    title = sub.exercise_title
                    break
            exercises.append(
                ExerciseSummaryDTO(
                    exercise_id=ex_id,
                    title=title,
                    order_index=idx + 1,
                )
            )
        return exercises

    def _evaluate_student(
        self,
        assignee: AssigneeUserInfo,
        homework: HomeworkEntity,
        coding_exercises: list[ExerciseSummaryDTO],
        db_exercise_map: dict[tuple[int, str], Any],
        db_coding_general_map: dict[int, Any],
        db_game_map: dict[int, Any],
        postpone_req: PermissionRequest | None,
        now: datetime,
    ) -> StudentHomeworkDetailDTO:
        """Đánh giá chi tiết tiến độ hoàn thành Coding & Game của 1 học sinh cụ thể."""
        user_id = assignee.user_id
        # Áp dụng Domain Rule: tính deadline hiệu lực khi có đơn gia hạn
        effective_deadline = homework.get_effective_deadline(
            postpone_req.start_time if postpone_req else None
        )
        is_past_effective = now > effective_deadline

        # 1. Đánh giá chi tiết từng bài coding con
        student_exercises: list[StudentExerciseStatusDTO] = []
        completed_coding_count = 0
        coding_has_late = False

        if coding_exercises:
            for ex in coding_exercises:
                sub = db_exercise_map.get((user_id, ex.exercise_id))
                if sub:
                    # Áp dụng Domain Rule: kiểm tra nộp trễ qua sub.is_late_for
                    is_late = sub.is_late_for(effective_deadline)
                    if is_late:
                        coding_has_late = True
                    if sub.is_passed:
                        completed_coding_count += 1

                    student_exercises.append(
                        StudentExerciseStatusDTO(
                            exercise_id=ex.exercise_id,
                            exercise_title=ex.title,
                            is_submitted=True,
                            is_passed=sub.is_passed,
                            score=sub.score,
                            attempt_number=sub.attempt_number or 1,
                            submitted_at=sub.submitted_at.isoformat()
                            if sub.submitted_at
                            else None,
                            is_late=is_late,
                        )
                    )
                else:
                    student_exercises.append(
                        StudentExerciseStatusDTO(
                            exercise_id=ex.exercise_id,
                            exercise_title=ex.title,
                            is_submitted=False,
                            is_passed=False,
                            score=None,
                            attempt_number=0,
                            submitted_at=None,
                            is_late=is_past_effective,
                        )
                    )
        else:
            if user_id in db_coding_general_map:
                completed_coding_count = 1

        # Áp dụng Domain Rule: xác định trạng thái hoàn thành coding
        coding_status_str = homework.determine_coding_status(
            completed_coding_count, len(coding_exercises)
        )

        # 2. Đánh giá trạng thái Game
        game_sub = db_game_map.get(user_id)
        game_is_submitted = game_sub is not None
        game_is_late = False
        game_submitted_at_str = None
        game_score = None

        if game_sub:
            # Áp dụng Domain Rule: kiểm tra nộp trễ game
            game_is_late = game_sub.is_late_for(effective_deadline)
            game_submitted_at_str = (
                game_sub.submitted_at.isoformat() if game_sub.submitted_at else None
            )
            game_score = game_sub.score

        return StudentHomeworkDetailDTO(
            user_id=user_id,
            name=assignee.name,
            avatar_url=assignee.avatar_url,
            total_coding_required=len(coding_exercises),
            total_coding_completed=completed_coding_count,
            coding_status=coding_status_str,
            coding_is_late=coding_has_late,
            coding_exercises=student_exercises,
            game_is_submitted=game_is_submitted,
            game_is_late=game_is_late,
            game_submitted_at=game_submitted_at_str,
            game_score=game_score,
        )

    def _calculate_exercise_completion_rates(
        self,
        exercises: list[ExerciseSummaryDTO],
        students: list[StudentHomeworkDetailDTO],
        total_assigned: int,
    ) -> None:
        """Tính toán số lượng và tỷ lệ % học sinh đã hoàn thành từng bài con."""
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
        """Phân nhóm học viên thành đã nộp / chưa nộp cho từng hạng mục Coding và Game."""
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
