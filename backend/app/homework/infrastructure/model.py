from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

import sqlmodel
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkStatus
from app.homework.domain.entity import HomeworkSubmission as HomeworkSubmissionEntity
from app.shared.infrastructure.base_model import TimestampMixin
from app.shared.domain.value_objects import UserRef
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class HomeworkSubmissionModel(TimestampMixin, table=True):
    """Homework submission model tracking user submissions"""

    __tablename__ = "homework_submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    homework_id: int = Field(foreign_key="homeworks.id", index=True)
    owner_id: int = Field(foreign_key="users.id", index=True)

    link: str = Field(default="", max_length=500)
    status: HomeworkStatus = Field(
        default=HomeworkStatus.NOT_SUBMITTED, sa_type=sqlmodel.String, index=True
    )
    is_late: bool = Field(default=False)

    is_pass: Optional[bool] = Field(default=None)
    score: Optional[float] = Field(default=None)
    feedback: Optional[str] = Field(default=None)
    score_details: Optional[list] = Field(default=None, sa_column=sqlmodel.Column(sqlmodel.JSON))
    plagiarism_info: Optional[list] = Field(default=None, sa_column=sqlmodel.Column(sqlmodel.JSON))
    is_plagiarized: bool = Field(default=False, sa_column_kwargs={"server_default": "false"})
    plagiarized_from_user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Relationships
    homework: "HomeworkModel" = Relationship(back_populates="submissions")
    owner: "UserModel" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[HomeworkSubmissionModel.owner_id]"}
    )

    def to_entity(self) -> HomeworkSubmissionEntity:
        from sqlalchemy import inspect

        ins = inspect(self)
        owner_ref = None
        if "owner" not in ins.unloaded and self.owner:
            owner_ref = UserRef(
                id=cast(int, self.owner.id),
                name=self.owner.name,
                avatar_url=self.owner.avatar_url,
            )

        homework_entity = None
        if "homework" not in ins.unloaded and self.homework:
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


class HomeworkModel(TimestampMixin, table=True):
    """Homework model containing assignment details"""

    __tablename__ = "homeworks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, index=True)
    deadline: datetime = Field(index=True)
    description: str  # Markdown text
    file_url: Optional[str] = Field(default=None)

    # Relationships
    submissions: List[HomeworkSubmissionModel] = Relationship(back_populates="homework")

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
    def from_entity(cls, entity: HomeworkEntity) -> "HomeworkModel":  # type: ignore[override]
        return cls(
            id=entity.id,
            title=entity.title,
            deadline=entity.deadline,
            description=entity.description,
            file_url=entity.file_url,
        )
