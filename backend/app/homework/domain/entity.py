from datetime import datetime
from typing import List, Optional

from app.homework.domain.value_objects import HomeworkStatus
from app.shared.domain.base_entity import BaseEntity


class HomeworkSubmission(BaseEntity):
    """Domain model tracking user submissions to homework."""

    homework_id: int
    owner_id: int
    link: str = ""
    status: HomeworkStatus = HomeworkStatus.NOT_SUBMITTED
    is_late: bool = False

    # Read-only attributes mapped from user relation
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    homework: Optional["Homework"] = None


class Homework(BaseEntity):
    """Domain model containing assignment details."""

    title: str
    description: str
    deadline: datetime
    file_url: Optional[str] = None
    submissions: List[HomeworkSubmission] = []

    @property
    def submission_count(self) -> int:
        return len(self.submissions)


HomeworkSubmission.model_rebuild()
Homework.model_rebuild()
