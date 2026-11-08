from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from app.shared.domain.event_bus import DomainEvent


class ScoreDetail(BaseModel):
    id: int
    criterion: str
    status: bool
    description: str
    weight: float


class HomeworkStatus(StrEnum):
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
    uncompleted_items: list[str] = []


class SubmissionEvaluation(BaseModel):
    is_submitted: bool
    is_overdue: bool
    coding_submitted: bool
    game_submitted: bool
    uncompleted_items: list[str]


class DueHomeworkAssignment(BaseModel):
    homework_id: int
    user_id: int
    homework_title: str
    deadline: datetime
    requires_coding: bool
    requires_game: bool
    slug: str = ""


class CodingScoreDetail(BaseModel):
    criterion: str | None = None
    status: bool = True
    score: float | None = None
    message: str | None = None


class CodingSubmissionDetails(BaseModel):
    submission_id: str | None = None
    original_filename: str | None = None
    status: str | None = None
    score_details: list[dict[str, Any]] | list[CodingScoreDetail] | None = None
    source: str = "webhook"


class GameSubmissionDetails(BaseModel):
    session_id: str | None = None
    final_score: float | None = None
    gold: int = 0
    total_questions: int = 0
    correct_count: int = 0
    attempt_count: int = 1
    source: str = "webhook"
