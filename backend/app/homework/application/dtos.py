from typing import Any
from datetime import datetime

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


class UserSubmissionInfo(BaseModel):
    user_id: int
    name: str | None = None
    avatar_url: str | None = None
    is_late: bool = False
    submitted_at: str | None = None


class CategorySubmissionStatus(BaseModel):
    submitted: list[UserSubmissionInfo] = []
    not_submitted: list[UserSubmissionInfo] = []


class HomeworkSubmissionStatusResponse(BaseModel):
    coding: CategorySubmissionStatus = CategorySubmissionStatus()
    game: CategorySubmissionStatus = CategorySubmissionStatus()

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
    submitted_at: datetime | None = None
    is_passed: bool = True
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
