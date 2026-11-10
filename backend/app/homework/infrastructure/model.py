from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)
from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    GameHomeworkSubmission,
    Homework as HomeworkEntity,
    HomeworkAssignee as HomeworkAssigneeEntity,
    HomeworkSubmission as HomeworkSubmissionEntity,
    SubmissionType,
)
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin


class SubmissionDetailsJSON(TypeDecorator):
    """
    SQLAlchemy TypeDecorator storing CodingSubmissionDetails or GameSubmissionDetails as JSON.
    Automatically handles Pydantic BaseModel serialization and deserialization.
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return {}
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if not value or not isinstance(value, dict):
            return None
        if "total_questions" in value or "correct_count" in value or "session_id" in value:
            return GameSubmissionDetails(**value)
        return CodingSubmissionDetails(**value)


class HomeworkModel(SQLAlchemyTimestampMixin, Base):
    """Homework model containing assignment details (Không còn cột deadline)"""

    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    link: Mapped[str | None] = mapped_column(String(500), default=None, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String, default=None, nullable=True)
    requires_coding: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    requires_game: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    assignees: Mapped[list["HomeworkAssigneeModel"]] = relationship(
        back_populates="homework", cascade="all, delete-orphan", lazy="selectin"
    )
    submissions: Mapped[list["HomeworkSubmissionModel"]] = relationship(
        back_populates="homework", cascade="all, delete-orphan", lazy="selectin"
    )

    def to_entity(self) -> HomeworkEntity:
        return HomeworkEntity(
            id=self.id,
            title=self.title,
            link=self.link,
            slug=self.slug,
            requires_coding=self.requires_coding,
            requires_game=self.requires_game,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: HomeworkEntity) -> "HomeworkModel":
        return cls(
            id=entity.id,
            title=entity.title,
            link=entity.link,
            slug=entity.slug,
            requires_coding=entity.requires_coding,
            requires_game=entity.requires_game,
        )


class HomeworkAssigneeModel(SQLAlchemyTimestampMixin, Base):
    """Mapping between Homework and direct User assignees with individual deadline"""

    __tablename__ = "homework_assignees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    homework: Mapped[HomeworkModel] = relationship(back_populates="assignees")

    def to_entity(self) -> HomeworkAssigneeEntity:
        return HomeworkAssigneeEntity(
            id=self.id,
            homework_id=self.homework_id,
            user_id=self.user_id,
            deadline=self.deadline,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: HomeworkAssigneeEntity) -> "HomeworkAssigneeModel":
        return cls(
            id=entity.id,
            homework_id=entity.homework_id,
            user_id=entity.user_id,
            deadline=entity.deadline,
        )


class HomeworkSubmissionModel(Base):
    """Append-only audit log of homework submission events."""

    __tablename__ = "homework_submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    submission_type: Mapped[str] = mapped_column(String(20), nullable=False)
    exercise_id: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True
    )
    exercise_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attempt_number: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    is_passed: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    details: Mapped[CodingSubmissionDetails | GameSubmissionDetails | None] = mapped_column(
        SubmissionDetailsJSON, default=None, server_default="{}", nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    homework: Mapped[HomeworkModel] = relationship(back_populates="submissions")

    __table_args__ = (
        Index(
            "ix_hw_submissions_lookup",
            "homework_id",
            "user_id",
            "exercise_id",
        ),
        Index(
            "idx_hw_submissions_lookup",
            "homework_id",
            "user_id",
            "submission_type",
            "submitted_at",
        ),
    )

    def to_entity(self) -> HomeworkSubmissionEntity:

        sub_type = (
            SubmissionType(self.submission_type.upper())
            if self.submission_type
            else SubmissionType.CODING
        )
        if sub_type == SubmissionType.GAME:
            return GameHomeworkSubmission(
                id=self.id,
                homework_id=self.homework_id,
                user_id=self.user_id,
                submission_type=SubmissionType.GAME,
                score=self.score,
                attempt_number=self.attempt_number or 1,
                submitted_at=self.submitted_at,
                is_passed=self.is_passed,
                details=self.details,
                created_at=self.created_at,
            )

        return CodingHomeworkSubmission(
            id=self.id,
            homework_id=self.homework_id,
            user_id=self.user_id,
            submission_type=SubmissionType.CODING,
            exercise_id=self.exercise_id or f"legacy-{self.homework_id}-{self.id}",
            exercise_title=self.exercise_title,
            score=self.score,
            attempt_number=self.attempt_number or 1,
            submitted_at=self.submitted_at,
            is_passed=self.is_passed,
            details=self.details,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: HomeworkSubmissionEntity) -> "HomeworkSubmissionModel":
        sub_type = (
            entity.submission_type.value
            if hasattr(entity.submission_type, "value")
            else str(entity.submission_type).upper()
        )
        return cls(
            id=entity.id,
            homework_id=entity.homework_id,
            user_id=entity.user_id,
            submission_type=sub_type,
            exercise_id=entity.exercise_id,
            exercise_title=entity.exercise_title,
            score=entity.score,
            attempt_number=entity.attempt_number,
            submitted_at=entity.submitted_at,
            is_passed=entity.is_passed,
            details=entity.details,
        )
