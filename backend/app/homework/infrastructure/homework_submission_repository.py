from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.homework.domain.entity import (
    HomeworkSubmission as HomeworkSubmissionEntity,
)
from app.homework.domain.entity import SubmissionType
from app.homework.domain.ports import HomeworkSubmissionRepositoryPort
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)
from app.homework.infrastructure.model import (
    HomeworkSubmissionModel,
)


class HomeworkSubmissionRepository(HomeworkSubmissionRepositoryPort):
    """Repository chuyên trách quản lý bảng lịch sử bài nộp homework_submissions (Append-Only)."""

    def __init__(self, session: Session):
        self.session = session

    def add_submission(
        self, submission: HomeworkSubmissionEntity
    ) -> HomeworkSubmissionEntity:
        """Insert a new immutable submission log into homework_submissions."""
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
        submission_type: SubmissionType | str,
        exercise_id: str | None = None,
        external_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmissionEntity | None:
        """
        Find an existing submission strictly for idempotent deduplication (append-only safe):
        1. Match by (homework_id, user_id, submission_type, external_submission_id) when external ID is present.
        2. Fallback to exact timestamp (+ exercise_id for CODING) ONLY when external_submission_id is absent.
        NEVER match CODING solely by (homework_id, user_id, exercise_id) to avoid overwriting earlier passed attempts.
        """
        type_str = str(
            submission_type.value
            if hasattr(submission_type, "value")
            else submission_type
        ).upper()

        # 1. Primary idempotent match by external_submission_id
        if external_submission_id:
            clean_ext_id = str(external_submission_id).strip()
            stmt = select(HomeworkSubmissionModel).where(
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.user_id == user_id,
                func.upper(HomeworkSubmissionModel.submission_type) == type_str,
                HomeworkSubmissionModel.external_submission_id == clean_ext_id,
            )
            found = self.session.scalars(stmt).first()
            if found:
                return found.to_entity()
            return None

        # 2. Fallback exact timestamp match when source does not provide external_submission_id
        if submitted_at:
            stmt = select(HomeworkSubmissionModel).where(
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.user_id == user_id,
                func.upper(HomeworkSubmissionModel.submission_type) == type_str,
                HomeworkSubmissionModel.submitted_at == submitted_at,
            )
            if exercise_id and type_str == "CODING":
                stmt = stmt.where(
                    HomeworkSubmissionModel.exercise_id == str(exercise_id)
                )
            found = self.session.scalars(stmt).first()
            if found:
                return found.to_entity()

        return None

    def update_submission(
        self,
        submission: HomeworkSubmissionEntity | HomeworkSubmissionModel,
        submitted_at: datetime | None = None,
        is_passed: bool | None = None,
        exercise_id: str | None = None,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int | None = None,
        details: CodingSubmissionDetails | GameSubmissionDetails | dict[str, Any] | None = None,
        external_submission_id: str | None = None,
    ) -> HomeworkSubmissionEntity:
        """Update an existing matched submission model and flush changes."""
        model = self._resolve_model(submission)
        field_updates = {
            "submitted_at": submitted_at,
            "is_passed": is_passed,
            "exercise_id": exercise_id,
            "external_submission_id": external_submission_id,
            "exercise_title": exercise_title,
            "score": score,
            "attempt_number": attempt_number,
        }
        for attr, val in field_updates.items():
            if val is not None:
                setattr(model, attr, val)

        if details is not None:
            model.details = self._merge_details(model, details)

        self.session.flush()
        return model.to_entity()

    def _resolve_model(
        self, submission: HomeworkSubmissionEntity | HomeworkSubmissionModel
    ) -> HomeworkSubmissionModel:
        if isinstance(submission, HomeworkSubmissionModel):
            return submission
        assert submission.id is not None
        loaded = self.session.get(HomeworkSubmissionModel, submission.id)
        if loaded is None:
            raise ValueError(
                f"HomeworkSubmission id={submission.id} not found for update"
            )
        return loaded

    @staticmethod
    def _merge_details(
        model: HomeworkSubmissionModel,
        details: CodingSubmissionDetails | GameSubmissionDetails | dict[str, Any],
    ) -> CodingSubmissionDetails | GameSubmissionDetails:
        current_dict = (
            model.details.model_dump()
            if isinstance(model.details, BaseModel)
            else dict(model.details or {})
        )
        update_dict = (
            details.model_dump()
            if isinstance(details, BaseModel)
            else dict(details)
        )
        current_dict.update(update_dict)
        if str(model.submission_type).upper() == "GAME":
            return GameSubmissionDetails(**current_dict)
        return CodingSubmissionDetails(**current_dict)

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
        """Get set of unique passed exercise_ids submitted by a user for a homework."""
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
