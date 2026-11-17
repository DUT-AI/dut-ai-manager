from datetime import datetime
from enum import StrEnum
from typing import Any, NamedTuple

from pydantic import BaseModel, ConfigDict, Field

from app.shared.domain.event_bus import DomainEvent


class AssigneeUserInfo(NamedTuple):
    user_id: int
    name: str
    avatar_url: str | None
    deadline: datetime


class CompletionStatus(StrEnum):
    """Mức độ hoàn thành bài tập (độc lập với tính đúng hạn)."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TimelinessStatus(StrEnum):
    """Tính đúng hạn so với hạn nộp cá nhân của học viên."""

    ON_TIME = "ON_TIME"
    LATE = "LATE"
    UPCOMING = "UPCOMING"
    OVERDUE = "OVERDUE"


class HomeworkAssigned(DomainEvent):
    homework_id: int
    assignee_ids: list[int]


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
    uncompleted_items: list[str] = Field(default_factory=list)
    deadline: datetime | None = None


class ExerciseEvaluation(BaseModel):
    """Kết quả đánh giá của một bài tập lập trình con bắt buộc đối với một học viên."""

    model_config = ConfigDict(frozen=True)

    exercise_id: str
    title: str
    order_index: int
    is_submitted: bool
    is_passed: bool
    first_passed_at: datetime | None = None
    latest_submitted_at: datetime | None = None
    best_score: float | None = None
    attempt_count: int = 0
    is_late: bool = False


class SubmissionEvaluation(BaseModel):
    """Kết quả đánh giá tổng hợp SSOT 2 chiều từ Homework.evaluate_submissions()."""

    completion_status: CompletionStatus = CompletionStatus.NOT_STARTED
    timeliness_status: TimelinessStatus = TimelinessStatus.UPCOMING
    is_submitted: bool
    is_completed_on_time: bool = False
    is_late: bool = False
    is_overdue: bool
    completed_at: datetime | None = None

    coding_submitted: bool
    coding_is_late: bool = False
    coding_status: str = "NOT_SUBMITTED"
    total_coding_required: int = 0
    total_coding_completed: int = 0
    coding_exercises: list[ExerciseEvaluation] = Field(default_factory=list)

    game_submitted: bool
    game_is_late: bool = False
    game_first_passed_at: datetime | None = None
    game_best_score: float | None = None

    uncompleted_items: list[str] = Field(default_factory=list)


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
