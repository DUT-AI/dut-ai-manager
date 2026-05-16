from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkStatus
from app.homework.domain.entity import HomeworkSubmission as HomeworkSubmissionEntity
from app.shared.domain.value_objects import UserRef
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class HomeworkSubmissionModel(SQLAlchemyTimestampMixin, Base):
    """Homework submission model tracking user submissions"""

    __tablename__ = "homework_submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    link: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[HomeworkStatus] = mapped_column(
        String(50), default=HomeworkStatus.NOT_SUBMITTED, index=True
    )
    is_late: Mapped[bool] = mapped_column(default=False)

    is_pass: Mapped[bool | None] = mapped_column(default=None)
    score: Mapped[float | None] = mapped_column(default=None)
    feedback: Mapped[str | None] = mapped_column(default=None)
    score_details: Mapped[list | None] = mapped_column(JSON, default=None)
    plagiarism_info: Mapped[list | None] = mapped_column(JSON, default=None)
    is_plagiarized: Mapped[bool] = mapped_column(default=False, server_default="false")
    plagiarized_from_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None, nullable=True
    )

    # Relationships
    homework: Mapped["HomeworkModel"] = relationship(back_populates="submissions")
    owner: Mapped["UserModel"] = relationship(foreign_keys=[owner_id])

    def to_entity(self) -> HomeworkSubmissionEntity:
        from sqlalchemy import inspect

        ins = inspect(self)
        owner_ref = None
        if ins is not None and "owner" not in ins.unloaded and self.owner:
            owner_ref = UserRef(
                id=self.owner.id,
                name=self.owner.name,
                avatar_url=self.owner.avatar_url,
            )

        homework_entity = None
        if ins is not None and "homework" not in ins.unloaded and self.homework:
            homework_entity = self.homework.to_entity()

        return HomeworkSubmissionEntity(
            id=self.id,
            homework_id=self.homework_id,
            owner_id=self.owner_id,
            link=self.link,
            status=self.status,
            is_late=self.is_late,
            is_pass=self.is_pass,
            score=self.score,
            feedback=self.feedback,
            score_details=self.score_details,
            plagiarism_info=self.plagiarism_info,
            is_plagiarized=self.is_plagiarized,
            plagiarized_from_user_id=self.plagiarized_from_user_id,
            owner=owner_ref,
            homework=homework_entity,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: HomeworkSubmissionEntity) -> "HomeworkSubmissionModel":
        return cls(
            id=entity.id,
            homework_id=entity.homework_id,
            owner_id=entity.owner_id,
            link=entity.link,
            status=entity.status,
            is_late=entity.is_late,
            is_pass=entity.is_pass,
            score=entity.score,
            feedback=entity.feedback,
            score_details=entity.score_details,
            plagiarism_info=entity.plagiarism_info,
            is_plagiarized=entity.is_plagiarized,
            plagiarized_from_user_id=entity.plagiarized_from_user_id,
        )


class HomeworkModel(SQLAlchemyTimestampMixin, Base):
    """Homework model containing assignment details"""

    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    deadline: Mapped[datetime] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(Text)
    file_url: Mapped[str | None] = mapped_column(default=None)

    # Relationships
    submissions: Mapped[list["HomeworkSubmissionModel"]] = relationship(
        back_populates="homework"
    )

    def to_entity(self) -> HomeworkEntity:
        from sqlalchemy import inspect

        ins = inspect(self)
        unloaded = getattr(ins, "unloaded", set())
        submissions_entities = []
        if "submissions" not in unloaded and self.submissions:
            for s in self.submissions:
                if not s.is_deleted:
                    submissions_entities.append(s.to_entity())

        return HomeworkEntity(
            id=self.id,
            title=self.title,
            deadline=self.deadline,
            description=self.description,
            file_url=self.file_url,
            submissions=submissions_entities,
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
            description=entity.description,
            file_url=entity.file_url,
        )
