from datetime import UTC, datetime
from enum import StrEnum

from app.homework.domain.value_objects import SubmissionEvaluation
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.datetime_types import ensure_utc


class SubmissionType(StrEnum):
    CODING = "CODING"
    GAME = "GAME"


class Homework(BaseEntity):
    """Domain model containing assignment details."""

    title: str
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = True
    requires_game: bool = False

    def evaluate_submissions(
        self,
        submissions: list["HomeworkSubmission"],
        reference_time: datetime | None = None,
    ) -> SubmissionEvaluation:
        """Aggregate Root đối chiếu danh sách bài nộp với yêu cầu của đề bài."""
        has_coding = self.requires_coding
        has_game = self.requires_game
        if not has_coding and not has_game:
            has_coding = True

        coding_submitted = any(
            getattr(s.submission_type, "value", str(s.submission_type)).upper()
            == "CODING"
            for s in submissions
        )
        game_submitted = any(
            getattr(s.submission_type, "value", str(s.submission_type)).upper()
            == "GAME"
            and s.is_passed is True
            for s in submissions
        )

        uncompleted: list[str] = []
        if has_coding and not coding_submitted:
            uncompleted.append("Bài tập Coding")
        if has_game and not game_submitted:
            uncompleted.append("Trắc nghiệm Game")

        is_submitted = (not has_coding or coding_submitted) and (
            not has_game or game_submitted
        )
        now = (
            ensure_utc(reference_time) if reference_time else datetime.now(UTC)
        )
        is_overdue = not is_submitted and (ensure_utc(self.deadline) < now)

        return SubmissionEvaluation(
            is_submitted=is_submitted,
            is_overdue=is_overdue,
            coding_submitted=coding_submitted,
            game_submitted=game_submitted,
            uncompleted_items=uncompleted,
        )

    def get_effective_deadline(self, postpone_time: datetime | None) -> datetime:
        """Domain Rule: Xác định deadline hiệu lực của học viên khi có đơn xin gia hạn."""
        base_dl = ensure_utc(self.deadline)
        if postpone_time:
            post_time = ensure_utc(postpone_time)
            if post_time > base_dl:
                return post_time
        return base_dl

    @staticmethod
    def determine_coding_status(completed_count: int, total_required: int) -> str:
        """Domain Rule: Quy tắc phân loại trạng thái hoàn thành coding."""
        if total_required <= 0:
            return "COMPLETED" if completed_count > 0 else "NOT_SUBMITTED"
        if completed_count >= total_required:
            return "COMPLETED"
        if completed_count > 0:
            return "PARTIALLY_SUBMITTED"
        return "NOT_SUBMITTED"

    def index_submissions(
        self, submissions: list["HomeworkSubmission"]
    ) -> tuple[
        dict[tuple[int, str], "HomeworkSubmission"],
        dict[int, "HomeworkSubmission"],
        dict[int, "HomeworkSubmission"],
    ]:
        """Aggregate Root: Phân loại và lập chỉ mục các bài nộp theo học viên và bài tập con."""
        exercise_map: dict[tuple[int, str], HomeworkSubmission] = {}
        coding_general_map: dict[int, HomeworkSubmission] = {}
        game_map: dict[int, HomeworkSubmission] = {}

        for sub in submissions:
            stype = (
                str(sub.submission_type).upper() if sub.submission_type else "CODING"
            )
            if stype == "CODING":
                if sub.exercise_id:
                    key = (sub.user_id, str(sub.exercise_id))
                    if key not in exercise_map or (
                        sub.is_passed and not exercise_map[key].is_passed
                    ):
                        exercise_map[key] = sub
                if sub.user_id not in coding_general_map or (
                    sub.is_passed and not coding_general_map[sub.user_id].is_passed
                ):
                    coding_general_map[sub.user_id] = sub
            elif stype == "GAME":
                if sub.user_id not in game_map or (
                    sub.is_passed and not game_map[sub.user_id].is_passed
                ):
                    game_map[sub.user_id] = sub

        return exercise_map, coding_general_map, game_map


class HomeworkSubmission(BaseEntity):
    """Base domain model representing a student homework submission attempt."""

    homework_id: int
    user_id: int
    submission_type: SubmissionType
    submitted_at: datetime
    is_passed: bool = True
    details: dict | None = None
    exercise_id: str | None = None
    exercise_title: str | None = None
    score: float | None = None
    attempt_number: int = 1

    def is_late_for(self, deadline: datetime) -> bool:
        """Domain Rule: Xác định bài nộp có bị trễ so với deadline hiệu lực không."""
        return ensure_utc(self.submitted_at) > ensure_utc(deadline)

    @property
    def is_coding(self) -> bool:
        return self.submission_type == SubmissionType.CODING

    @property
    def is_game(self) -> bool:
        return self.submission_type == SubmissionType.GAME

    @classmethod
    def create_coding(
        cls,
        homework_id: int,
        user_id: int,
        exercise_id: str,
        submitted_at: datetime,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int = 1,
        is_passed: bool = True,
        details: dict | None = None,
        id: int | None = None,
    ) -> "CodingHomeworkSubmission":
        """Factory method to create a strict, strongly-typed Coding submission."""
        return CodingHomeworkSubmission(
            id=id,
            homework_id=homework_id,
            user_id=user_id,
            submission_type=SubmissionType.CODING,
            exercise_id=exercise_id,
            exercise_title=exercise_title,
            score=score,
            attempt_number=attempt_number,
            submitted_at=submitted_at,
            is_passed=is_passed,
            details=details,
        )

    @classmethod
    def create_game(
        cls,
        homework_id: int,
        user_id: int,
        submitted_at: datetime,
        score: float | None = None,
        attempt_number: int = 1,
        is_passed: bool = True,
        details: dict | None = None,
        id: int | None = None,
    ) -> "GameHomeworkSubmission":
        """Factory method to create a Game quiz submission."""
        return GameHomeworkSubmission(
            id=id,
            homework_id=homework_id,
            user_id=user_id,
            submission_type=SubmissionType.GAME,
            score=score,
            attempt_number=attempt_number,
            submitted_at=submitted_at,
            is_passed=is_passed,
            details=details,
        )


class CodingHomeworkSubmission(HomeworkSubmission):
    """
    Domain model for a specific coding exercise submission.
    `exercise_id` is mandatory (non-null) to guarantee exact exercise tracking.
    """

    submission_type: SubmissionType = SubmissionType.CODING
    exercise_id: str  # BẮT BUỘC 100%, không thể None
    exercise_title: str | None = None
    score: float | None = None
    attempt_number: int = 1


class GameHomeworkSubmission(HomeworkSubmission):
    """
    Domain model for an interactive quiz game session attempt.
    """

    submission_type: SubmissionType = SubmissionType.GAME
    score: float | None = None
    attempt_number: int = 1
