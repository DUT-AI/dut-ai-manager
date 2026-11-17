from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.homework.application.dtos.common import ExerciseSummaryDTO
from app.homework.domain.entity import HomeworkSubmission, SubmissionType
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


class MyHomeworkExerciseStatusDTO(BaseModel):
    """Trạng thái chi tiết của 1 bài tập coding con bắt buộc cho màn hình học viên."""

    exercise_id: str
    title: str
    order_index: int = 0
    is_submitted: bool = False
    is_passed: bool = False
    first_passed_at: datetime | None = None
    latest_submitted_at: datetime | None = None
    best_score: float | None = None
    attempt_count: int = 0
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
        if isinstance(data, HomeworkSubmission):
            sub_type = str(data.submission_type).upper()
            raw_details = data.details
            if isinstance(raw_details, (CodingSubmissionDetails, GameSubmissionDetails)):
                parsed_details = raw_details
            elif isinstance(raw_details, dict):
                parsed_details = (
                    GameSubmissionDetails(**raw_details)
                    if sub_type == "GAME"
                    else CodingSubmissionDetails(**raw_details)
                )
            else:
                parsed_details = (
                    GameSubmissionDetails()
                    if sub_type == "GAME"
                    else CodingSubmissionDetails()
                )
            return {
                "id": data.id,
                "homework_id": data.homework_id,
                "user_id": data.user_id,
                "submission_type": data.submission_type,
                "exercise_id": data.exercise_id,
                "exercise_title": data.exercise_title,
                "score": data.score,
                "attempt_number": data.attempt_number or 1,
                "submitted_at": data.submitted_at,
                "is_passed": data.is_passed,
                "details": parsed_details,
                "created_at": data.created_at,
            }

        if isinstance(data, dict):
            raw_details = data.get("details")
            sub_type = str(data.get("submission_type", "")).upper()
            if not isinstance(raw_details, (CodingSubmissionDetails, GameSubmissionDetails)):
                detail_dict = raw_details if isinstance(raw_details, dict) else {}
                if sub_type == "GAME":
                    data["details"] = GameSubmissionDetails(**detail_dict)
                else:
                    data["details"] = CodingSubmissionDetails(**detail_dict)
            return data

        return data


class HomeworkWebhookResponse(BaseModel):
    """Phản hồi chuẩn từ Webhook nộp bài tập."""

    status: str  # "recorded" | "updated" | "ignored"
    message: str | None = None
    reason: str | None = None
    submission_id: int | None = None
    homework_id: int | None = None
    user_id: int | None = None
    exercise_id: str | None = None

    model_config = ConfigDict(from_attributes=True)

    def __getitem__(self, item: str) -> Any:
        """Hỗ trợ backward-compatibility truy cập theo kiểu dict key."""
        return getattr(self, item)


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

    details: CodingSubmissionDetails | GameSubmissionDetails | None = None

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

    @model_validator(mode="before")
    @classmethod
    def parse_submission_details(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_details = data.get("details")
            sub_type = data.get("type")
            if isinstance(sub_type, str):
                sub_type_str = sub_type.strip().upper()
            elif isinstance(sub_type, SubmissionType):
                sub_type_str = sub_type.value.upper()
            else:
                sub_type_str = "CODING"

            if raw_details is not None and not isinstance(
                raw_details, (CodingSubmissionDetails, GameSubmissionDetails)
            ):
                if isinstance(raw_details, dict):
                    if sub_type_str == "GAME":
                        data["details"] = GameSubmissionDetails(**raw_details)
                    else:
                        data["details"] = CodingSubmissionDetails(**raw_details)
        return data
