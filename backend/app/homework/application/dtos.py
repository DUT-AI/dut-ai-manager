from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.homework.domain.entity import SubmissionType
from app.shared.domain.value_objects import UserRef


class HomeworkBase(BaseModel):
    title: str
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = False
    requires_game: bool = False


class HomeworkCreate(HomeworkBase):
    assignee_ids: list[int] = Field(default_factory=list)


class HomeworkUpdate(BaseModel):
    title: str | None = None
    deadline: datetime | None = None
    link: str | None = None
    slug: str | None = None
    requires_coding: bool | None = None
    requires_game: bool | None = None
    assignee_ids: list[int] | None = None


class HomeworkResponse(HomeworkBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    assignee_ids: list[int] = []

    # Computed fields (populated by use cases)
    submission_count: int = 0
    is_submitted: bool | None = None
    is_overdue: bool | None = None
    has_coding: bool = False
    coding_submitted: bool = False
    has_game: bool = False
    game_submitted: bool = False
    uncompleted_items: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ExerciseSummaryDTO(BaseModel):
    """Thông tin tóm tắt của một bài tập coding con kèm số liệu hoàn thành."""

    exercise_id: str
    title: str
    order_index: int = 0
    completed_count: int = 0
    total_assigned: int = 0
    completion_rate: float = 0.0


class StudentExerciseStatusDTO(BaseModel):
    """Trạng thái nộp bài của 1 học viên đối với 1 bài tập coding con."""

    exercise_id: str
    exercise_title: str
    is_submitted: bool = False
    is_passed: bool = False
    score: float | None = None
    attempt_number: int = 0
    submitted_at: str | None = None
    is_late: bool = False


class StudentHomeworkDetailDTO(BaseModel):
    """Tiến độ nộp bài tổng thể của 1 học viên được phân công."""

    user_id: int
    name: str | None = None
    avatar_url: str | None = None

    # Tiến độ Coding
    total_coding_required: int = 0
    total_coding_completed: int = 0
    coding_status: str = (
        "NOT_SUBMITTED"  # "COMPLETED" | "PARTIALLY_SUBMITTED" | "NOT_SUBMITTED"
    )
    coding_is_late: bool = False
    coding_exercises: list[StudentExerciseStatusDTO] = Field(default_factory=list)

    # Tiến độ Game
    game_is_submitted: bool = False
    game_is_late: bool = False
    game_submitted_at: str | None = None
    game_score: float | None = None


class UserSubmissionInfo(BaseModel):
    user_id: int
    name: str | None = None
    avatar_url: str | None = None
    is_late: bool = False
    submitted_at: str | None = None
    total_coding_required: int = 0
    total_coding_completed: int = 0
    coding_status: str = "NOT_SUBMITTED"
    coding_exercises: list[StudentExerciseStatusDTO] = Field(default_factory=list)


class CategorySubmissionStatus(BaseModel):
    submitted: list[UserSubmissionInfo] = []
    not_submitted: list[UserSubmissionInfo] = []


class HomeworkSubmissionStatusResponse(BaseModel):
    coding: CategorySubmissionStatus = CategorySubmissionStatus()
    game: CategorySubmissionStatus = CategorySubmissionStatus()

    # Danh sách bài tập con của bài học
    coding_exercises: list[ExerciseSummaryDTO] = Field(default_factory=list)

    # Chi tiết theo từng học viên
    students: list[StudentHomeworkDetailDTO] = Field(default_factory=list)

    # Top-level combined fields for fallback
    submitted: list[UserSubmissionInfo] = []
    not_submitted: list[UserSubmissionInfo] = []


class HomeworkReportResponse(BaseModel):
    user_id: int
    owner: UserRef | None = None
    unsubmitted_count: int = 0


class HomeworkSubmissionDetailResponse(BaseModel):
    id: int
    homework_id: int
    user_id: int
    submission_type: SubmissionType
    exercise_id: str | None = None
    exercise_title: str | None = None
    score: float | None = None
    attempt_number: int = 1
    submitted_at: datetime | None = None
    is_passed: bool = True
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
