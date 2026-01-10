import sqlmodel
from enum import Enum
from typing import TYPE_CHECKING, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.homework import Homework


class HomeworkStatus(str, Enum):
    NOT_SUBMITTED = "chưa nộp"
    SUBMITTED = "đã nộp"
    LEADER_CHECKED = "leader đã check"
    FINISHED = "finish"


class HomeworkSubmission(TimestampMixin, table=True):
    """Homework submission model tracking user submissions"""

    __tablename__ = "homework_submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    homework_id: int = Field(foreign_key="homeworks.id", index=True)

    link: str = Field(max_length=500)
    status: HomeworkStatus = Field(
        default=HomeworkStatus.NOT_SUBMITTED, sa_type=sqlmodel.String
    )
    is_late: bool = Field(default=False)

    # Relationships
    homework: "Homework" = Relationship(back_populates="submissions")
    owner: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[HomeworkSubmission.created_by]"}
    )

    @property
    def user_name(self) -> Optional[str]:
        return self.owner.name if self.owner else None
