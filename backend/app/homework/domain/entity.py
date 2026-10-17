from app.utils.datetime import get_current_utc7_time
from datetime import datetime
from enum import StrEnum

import httpx
from loguru import logger

from app.core.config import settings
from app.shared.domain.base_entity import BaseEntity
from app.homework.domain.value_objects import SubmissionEvaluation

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
    assignee_ids: list[int] = []

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
        now = reference_time or get_current_utc7_time()
        is_overdue = not is_submitted and (self.deadline < now)

        return SubmissionEvaluation(
            is_submitted=is_submitted,
            is_overdue=is_overdue,
            coding_submitted=coding_submitted,
            game_submitted=game_submitted,
            uncompleted_items=uncompleted,
        )


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
