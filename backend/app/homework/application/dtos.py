from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.homework.domain.entity import SubmissionType
from app.homework.domain.value_objects import (
    CodingScoreDetail,
    CodingSubmissionDetails,
    GameSubmissionDetails,
)
from app.shared.domain.datetime_types import UtcDateTime
from app.shared.domain.value_objects import UserRef


class HomeworkBase(BaseModel):
    title: str
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = False
    requires_game: bool = False


class HomeworkCreate(HomeworkBase):
    deadline: UtcDateTime
    assignee_ids: list[int] = Field(default_factory=list)


class HomeworkUpdate(BaseModel):
    title: str | None = None
    deadline: UtcDateTime | None = None
    link: str | None = None
    slug: str | None = None
    requires_coding: bool | None = None
    requires_game: bool | None = None
    assignee_ids: list[int] | None = None
    force_override_deadlines: bool = False


class HomeworkResponse(HomeworkBase):
    id: int
    deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

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

    @classmethod
    def from_domain(
        cls, hw: Any, deadline: datetime | None = None
    ) -> "HomeworkResponse":
        return cls(
            id=hw.id,
            title=hw.title,
            deadline=deadline,
            link=hw.link,
            slug=hw.slug,
            requires_coding=hw.requires_coding,
            requires_game=hw.requires_game,
            created_at=hw.created_at,
            updated_at=hw.updated_at,
            created_by=hw.created_by,
        )

    from_entity = from_domain


class ExerciseSummaryDTO(BaseModel):
    """Thông tin tóm tắt của một bài tập coding con kèm số liệu hoàn thành."""

    exercise_id: str
    title: str
    order_index: int = 0
    completed_count: int = 0
    total_assigned: int = 0
    completion_rate: float = 0.0


class HomeworkResponseDetail(HomeworkResponse):
    """DTO chi tiết bài tập bao gồm danh sách assignee_ids phục vụ màn hình chỉnh sửa/chi tiết."""

    assignee_ids: list[int] = Field(default_factory=list)
    coding_exercises: list[ExerciseSummaryDTO] = Field(default_factory=list)

    @classmethod
    def from_domain(
        cls,
        hw: Any,
        assignee_ids: list[int] | None = None,
        deadline: datetime | None = None,
        coding_exercises: list[ExerciseSummaryDTO] | None = None,
    ) -> "HomeworkResponseDetail":
        return cls(
            id=hw.id,
            title=hw.title,
            deadline=deadline,
            link=hw.link,
            slug=hw.slug,
            requires_coding=hw.requires_coding,
            requires_game=hw.requires_game,
            created_at=hw.created_at,
            updated_at=hw.updated_at,
            created_by=hw.created_by,
            assignee_ids=assignee_ids or [],
            coding_exercises=coding_exercises or [],
        )

    from_entity = from_domain


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
    details: CodingSubmissionDetails | GameSubmissionDetails
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def parse_typed_details(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_details = data.get("details") or {}
            sub_type = str(data.get("submission_type", "")).upper()
            if not isinstance(raw_details, (CodingSubmissionDetails, GameSubmissionDetails)):
                if sub_type == "GAME":
                    data["details"] = GameSubmissionDetails(**raw_details)
                else:
                    data["details"] = CodingSubmissionDetails(**raw_details)
        elif hasattr(data, "submission_type") and hasattr(data, "details"):
            # ORM Model or Domain Entity
            sub_type = getattr(data.submission_type, "value", str(data.submission_type)).upper()
            raw_details = getattr(data, "details", {}) or {}
            if not isinstance(raw_details, (CodingSubmissionDetails, GameSubmissionDetails)):
                parsed_details = (
                    GameSubmissionDetails(**raw_details)
                    if sub_type == "GAME"
                    else CodingSubmissionDetails(**raw_details)
                )
                # If data is an object, convert to dict for Pydantic instantiation
                return {
                    "id": getattr(data, "id", None),
                    "homework_id": getattr(data, "homework_id", None),
                    "user_id": getattr(data, "user_id", None),
                    "submission_type": getattr(data, "submission_type", None),
                    "exercise_id": getattr(data, "exercise_id", None),
                    "exercise_title": getattr(data, "exercise_title", None),
                    "score": getattr(data, "score", None),
                    "attempt_number": getattr(data, "attempt_number", 1) or 1,
                    "submitted_at": getattr(data, "submitted_at", None),
                    "is_passed": getattr(data, "is_passed", True),
                    "details": parsed_details,
                    "created_at": getattr(data, "created_at", None),
                }
        return data


class SyncHomeworkResult(BaseModel):
    """Kết quả phản hồi chi tiết sau khi đồng bộ bài tập từ Quiz API."""

    homework_id: int
    title: str
    requires_coding: bool
    requires_game: bool
    coding_exercises_count: int = 0
    game_questions_count: int = 0
    synced_coding_count: int = 0
    updated_coding_count: int = 0
    synced_game_count: int = 0
    updated_game_count: int = 0
    message: str

    model_config = ConfigDict(from_attributes=True)
