from enum import Enum

from app.shared.domain.event_bus import DomainEvent


class HomeworkStatus(str, Enum):
    NOT_SUBMITTED = "chưa nộp"
    SUBMITTED = "đã nộp"
    LEADER_CHECKED = "leader đã check"
    FINISHED = "finish"


class HomeworkAssigned(DomainEvent):
    homework_id: int
    assignee_ids: list[int]


class HomeworkSubmitted(DomainEvent):
    homework_id: int
    user_id: int
    is_late: bool
