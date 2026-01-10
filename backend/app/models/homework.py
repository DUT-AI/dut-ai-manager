from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class Homework(TimestampMixin, table=True):
    """Homework model containing assignment details"""

    __tablename__ = "homeworks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, index=True)
    deadline: datetime
    description: str  # Markdown text

    # Relationships
    submissions: List["HomeworkSubmission"] = Relationship(back_populates="homework")
    assignees: List["HomeworkAssignee"] = Relationship(back_populates="homework")


class HomeworkAssignee(TimestampMixin, table=True):
    """Junction table for assigning homework to specific users"""

    __tablename__ = "homework_assignees"

    homework_id: int = Field(foreign_key="homeworks.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)

    # Relationships
    homework: Homework = Relationship(back_populates="assignees")
    user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[HomeworkAssignee.user_id]"}
    )
