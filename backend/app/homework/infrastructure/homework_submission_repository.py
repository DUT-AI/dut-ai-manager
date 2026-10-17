from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.homework.domain.entity import (
    HomeworkSubmission as HomeworkSubmissionEntity,
)
from app.homework.infrastructure.model import (
    HomeworkSubmissionModel,
)


class HomeworkSubmissionRepository:
    """Repository chuyên trách quản lý bảng bài nộp homework_submissions."""

    def __init__(self, session: Session):
        self.session = session

    def add_submission(
        self, submission: HomeworkSubmissionEntity
    ) -> HomeworkSubmissionEntity:
        """Insert a new submission log into homework_submissions."""
        model = HomeworkSubmissionModel.from_entity(submission)
        self.session.add(model)
        self.session.flush()
        return model.to_entity()

    def get_submissions_by_user(
        self, homework_id: int, user_id: int
    ) -> list[HomeworkSubmissionEntity]:
        """Get all submission history of a user for a specific homework ordered by time descending."""
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.user_id == user_id,
            )
            .order_by(desc(HomeworkSubmissionModel.submitted_at))
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_user_submissions_for_homeworks(
        self, homework_ids: list[int], user_id: int
    ) -> list[HomeworkSubmissionEntity]:
        """Get all submissions of a user across multiple homework IDs."""
        if not homework_ids:
            return []
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.homework_id.in_(homework_ids),
                HomeworkSubmissionModel.user_id == user_id,
            )
            .order_by(desc(HomeworkSubmissionModel.submitted_at))
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_all_submissions(self) -> list[HomeworkSubmissionEntity]:
        """Get all submissions in the database."""
        statement = select(HomeworkSubmissionModel)
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def has_valid_submission(
        self,
        homework_id: int,
        user_id: int,
        submission_type: Any,
        deadline: datetime,
    ) -> bool:
        """
        Check if user has at least one valid submission before or at deadline.
        For coding: is_passed is always True.
        For game: requires is_passed == True.
        """
        type_str = str(
            submission_type.value
            if hasattr(submission_type, "value")
            else submission_type
        ).upper()
        statement = select(HomeworkSubmissionModel.id).where(
            HomeworkSubmissionModel.homework_id == homework_id,
            HomeworkSubmissionModel.user_id == user_id,
            func.upper(HomeworkSubmissionModel.submission_type) == type_str,
            HomeworkSubmissionModel.is_passed == True,
            HomeworkSubmissionModel.submitted_at <= deadline,
        )
        return self.session.scalars(statement).first() is not None

    def get_submissions_by_homework(
        self, homework_id: int
    ) -> list[HomeworkSubmissionEntity]:
        """Get all submissions for a homework."""
        statement = (
            select(HomeworkSubmissionModel)
            .where(HomeworkSubmissionModel.homework_id == homework_id)
            .order_by(desc(HomeworkSubmissionModel.submitted_at))
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def find_submission_match(
        self,
        homework_id: int,
        user_id: int,
        submission_type: Any,
        exercise_id: str | None = None,
        quiz_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmissionModel | None:
        """
        Find an existing submission by exercise_id, quiz_submission_id (in details JSON),
        or by exact (homework_id, user_id, submission_type, submitted_at).
        """
        type_str = str(
            submission_type.value
            if hasattr(submission_type, "value")
            else submission_type
        ).upper()

        # 1. Tìm theo exercise_id đối với bài tập CODING
        if exercise_id and type_str == "CODING":
            stmt = select(HomeworkSubmissionModel).where(
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.user_id == user_id,
                HomeworkSubmissionModel.exercise_id == exercise_id,
            )
            found = self.session.scalars(stmt).first()
            if found:
                return found

        # 2. Tìm theo quiz_submission_id (nếu có)
        if quiz_submission_id:
            try:
                stmt = select(HomeworkSubmissionModel).where(
                    HomeworkSubmissionModel.homework_id == homework_id,
                    HomeworkSubmissionModel.user_id == user_id,
                    func.upper(HomeworkSubmissionModel.submission_type) == type_str,
                    HomeworkSubmissionModel.details["submission_id"].astext
                    == str(quiz_submission_id),
                )
                found = self.session.scalars(stmt).first()
                if found:
                    return found
            except Exception:
                pass

        # 3. Tìm theo submitted_at chính xác
        if submitted_at:
            stmt = select(HomeworkSubmissionModel).where(
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.user_id == user_id,
                func.upper(HomeworkSubmissionModel.submission_type) == type_str,
                HomeworkSubmissionModel.submitted_at == submitted_at,
            )
            found = self.session.scalars(stmt).first()
            if found:
                return found

        return None

    def update_submission(
        self,
        model: HomeworkSubmissionModel,
        submitted_at: datetime | None = None,
        is_passed: bool | None = None,
        exercise_id: str | None = None,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int | None = None,
        details: dict | None = None,
    ) -> HomeworkSubmissionEntity:
        """Update an existing submission model and flush changes."""
        if submitted_at is not None:
            model.submitted_at = submitted_at
        if is_passed is not None:
            model.is_passed = is_passed
        if exercise_id is not None:
            model.exercise_id = exercise_id
        if exercise_title is not None:
            model.exercise_title = exercise_title
        if score is not None:
            model.score = score
        if attempt_number is not None:
            model.attempt_number = attempt_number
        if details is not None:
            current_details = dict(model.details or {})
            current_details.update(details)
            model.details = current_details
        self.session.flush()
        return model.to_entity()

    def get_submissions_by_exercise(
        self, homework_id: int, exercise_id: str
    ) -> list[HomeworkSubmissionEntity]:
        """Get all submissions for a specific exercise under a homework."""
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.exercise_id == exercise_id,
            )
            .order_by(desc(HomeworkSubmissionModel.submitted_at))
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_submitted_exercise_ids(
        self,
        homework_id: int,
        user_id: int,
        deadline: datetime | None = None,
    ) -> set[str]:
        """Get set of unique exercise_ids submitted by a user for a homework."""
        statement = select(HomeworkSubmissionModel.exercise_id).where(
            HomeworkSubmissionModel.homework_id == homework_id,
            HomeworkSubmissionModel.user_id == user_id,
            func.upper(HomeworkSubmissionModel.submission_type) == "CODING",
            HomeworkSubmissionModel.is_passed == True,
            HomeworkSubmissionModel.exercise_id.is_not(None),
        )
        if deadline is not None:
            statement = statement.where(
                HomeworkSubmissionModel.submitted_at <= deadline
            )
        results = self.session.scalars(statement).all()
        return {str(eid) for eid in results if eid}
