from enum import Enum

from pydantic import BaseModel

from app.shared.domain.event_bus import DomainEvent


class ScoreDetail(BaseModel):
    id: int
    criterion: str
    status: bool
    description: str
    weight: float


class HomeworkStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    LEADER_CHECKED = "LEADER_CHECKED"
    FINISHED = "FINISHED"


class HomeworkAssigned(DomainEvent):
    homework_id: int
    assignee_ids: list[int]


class HomeworkSubmitted(DomainEvent):
    homework_id: int
    user_id: int
    is_late: bool


class HomeworkGraded(DomainEvent):
    homework_id: int
    user_id: int
    score: float | None
    is_pass: bool | None
    is_plagiarized: bool


class HomeworkOverdueDetected(DomainEvent):
    user_id: int
    homework_id: int
    homework_title: str
    deadline_date: str
    reason: str = "Không nộp bài tập"
