from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.homework.domain.entity import (
    Homework as HomeworkEntity,
)
from app.homework.domain.entity import (
    HomeworkSubmission as HomeworkSubmissionEntity,
)
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.utils.datetime import get_current_utc7_time


class HomeworkModel(SQLAlchemyTimestampMixin, Base):
    """Homework model containing assignment details"""

    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    deadline: Mapped[datetime] = mapped_column(index=True)
    link: Mapped[str | None] = mapped_column(String(500), default=None, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True)
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
        assignee_ids = []
        if "assignees" in self.__dict__ and self.assignees:
            assignee_ids = [a.user_id for a in self.assignees]

        return HomeworkEntity(
            id=self.id,
            title=self.title,
            deadline=self.deadline,
            link=self.link,
            slug=self.slug,
            requires_coding=self.requires_coding,
            requires_game=self.requires_game,
            assignee_ids=assignee_ids,
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
            deadline=entity.deadline,
            link=entity.link,
            slug=entity.slug,
            requires_coding=entity.requires_coding,
            requires_game=entity.requires_game,
        )


class HomeworkAssigneeModel(SQLAlchemyTimestampMixin, Base):
    """Mapping between Homework and direct User assignees"""

    __tablename__ = "homework_assignees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    homework: Mapped[HomeworkModel] = relationship(back_populates="assignees")


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
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_current_utc7_time, nullable=False
    )
    is_passed: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    details: Mapped[dict | None] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_current_utc7_time, nullable=False
    )

    homework: Mapped[HomeworkModel] = relationship(back_populates="submissions")

    def to_entity(self) -> HomeworkSubmissionEntity:
        from app.homework.domain.entity import SubmissionType

        sub_type = (
            SubmissionType(self.submission_type.upper())
            if self.submission_type
            else SubmissionType.CODING
        )
        return HomeworkSubmissionEntity(
            id=self.id,
            homework_id=self.homework_id,
            user_id=self.user_id,
            submission_type=sub_type,
            submitted_at=self.submitted_at,
            is_passed=self.is_passed,
            details=self.details or {},
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
            submitted_at=entity.submitted_at,
            is_passed=entity.is_passed,
            details=entity.details or {},
        )
