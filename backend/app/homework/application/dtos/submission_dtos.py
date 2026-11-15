from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.homework.application.dtos.common import ExerciseSummaryDTO
from app.homework.domain.entity import SubmissionType
from app.homework.domain.value_objects import (
    CodingSubmissionDetails,
    GameSubmissionDetails,
)
from app.shared.domain.datetime_types import UtcDateTime


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

    # Tổng số học sinh đã hoàn thành đầy đủ tất cả các phần bài tập được yêu cầu
    total_completed_count: int = 0

    # Danh sách bài tập con của bài học
    coding_exercises: list[ExerciseSummaryDTO] = Field(default_factory=list)

    # Chi tiết theo từng học viên
    students: list[StudentHomeworkDetailDTO] = Field(default_factory=list)


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
            return data

        # ORM Model or Domain Entity
        sub_type_raw = getattr(data, "submission_type", None)
        if sub_type_raw is not None:
            sub_type = getattr(sub_type_raw, "value", str(sub_type_raw)).upper()
            raw_details = getattr(data, "details", {}) or {}
            if not isinstance(raw_details, (CodingSubmissionDetails, GameSubmissionDetails)):
                parsed_details = (
                    GameSubmissionDetails(**raw_details)
                    if sub_type == "GAME"
                    else CodingSubmissionDetails(**raw_details)
                )
                return {
                    "id": getattr(data, "id", None),
                    "homework_id": getattr(data, "homework_id", None),
                    "user_id": getattr(data, "user_id", None),
                    "submission_type": sub_type_raw,
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


class HomeworkSubmissionWebhookIn(BaseModel):
    """Payload schema nhận từ Quiz Webhook khi có sự kiện nộp bài hoặc hoàn thành game."""

    lesson_slug: str
    user_id: int
    type: SubmissionType
    submitted_at: UtcDateTime
    is_passed: bool = True

    # Chi tiết bài tập con (dành cho CODING)
    exercise_id: str | None = None
    exercise_title: str | None = None
    submission_id: str | None = None
    attempt_number: int = 1
    score: float | None = None
    original_filename: str | None = None

    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("type", mode="before")
    @classmethod
    def parse_submission_type(cls, v: Any) -> SubmissionType:
        if isinstance(v, SubmissionType):
            return v
        if isinstance(v, str):
            val = v.strip().upper()
            if val in SubmissionType.__members__:
                return SubmissionType[val]
        raise ValueError(f"Invalid submission type: {v}. Must be CODING or GAME")
