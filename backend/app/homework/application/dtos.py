from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.homework.domain.entity import HomeworkStatus
from app.homework.domain.value_objects import ScoreDetail
from app.shared.domain.value_objects import UserRef


class HomeworkBase(BaseModel):
    title: str
    description: str
    deadline: datetime
    file_url: str | None = None


class HomeworkCreate(HomeworkBase):
    assignee_ids: list[int] | None = None
    team_ids: list[int] | None = None  # Query users from these teams


class HomeworkUpdate(BaseModel):
    title: str
    description: str | None = None
    deadline: datetime | None = None
    file_url: str | None = None
    assignee_ids: list[int] | None = None  # Sync assignees
    team_ids: list[int] | None = None  # Add users from teams


class HomeworkResponse(HomeworkBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    # Computed fields (can be populated by service/repo)
    submission_count: int = 0

    class Config:
        from_attributes = True


class HomeworkSubmissionCreate(BaseModel):
    link: HttpUrl


class HomeworkSubmissionUpdate(BaseModel):
    link: HttpUrl | None = None
    status: HomeworkStatus | None = None


class HomeworkSubmissionResponse(BaseModel):
    id: int
    homework_id: int
    owner_id: int
    owner: UserRef | None = None
    created_by: int | None = None
    link: str
    status: HomeworkStatus
    is_late: bool
    is_pass: bool | None = None
    score: float | None = None
    feedback: str | None = None
    score_details: list[ScoreDetail] | None = None
    plagiarism_info: list[dict] | None = None
    is_plagiarized: bool = False
    plagiarized_from_user_id: int | None = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HomeworkReportResponse(BaseModel):
    user_id: int
    owner: UserRef | None = None
    unsubmitted_count: int
