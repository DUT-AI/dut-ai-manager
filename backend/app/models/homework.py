from datetime import datetime
from typing import List, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.homework_submission import HomeworkSubmission


class Homework(TimestampMixin, table=True):
    """Homework model containing assignment details"""

    __tablename__ = "homeworks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, index=True)
    deadline: datetime = Field(index=True)
    description: str  # Markdown text
    file_url: Optional[str] = Field(default=None)

    # Relationships
    submissions: List["HomeworkSubmission"] = Relationship(back_populates="homework")
