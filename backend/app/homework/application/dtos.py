from datetime import datetime
from typing import List, Optional

from app.homework.domain.entity import HomeworkStatus
from app.homework.domain.value_objects import ScoreDetail
from pydantic import BaseModel, HttpUrl


class HomeworkBase(BaseModel):
    title: str
    description: str
    deadline: datetime
    file_url: Optional[str] = None


class HomeworkCreate(HomeworkBase):
    assignee_ids: Optional[List[int]] = None
    team_ids: Optional[List[int]] = None  # Query users from these teams


class HomeworkUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    file_url: Optional[str] = None
    assignee_ids: Optional[List[int]] = None  # Sync assignees
    team_ids: Optional[List[int]] = None  # Add users from teams


class HomeworkResponse(HomeworkBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    # Computed fields (can be populated by service/repo)
    submission_count: int = 0

    class Config:
        from_attributes = True


class HomeworkSubmissionCreate(BaseModel):
    link: HttpUrl


class HomeworkSubmissionUpdate(BaseModel):
    link: Optional[HttpUrl] = None
    status: Optional[HomeworkStatus] = None


class HomeworkSubmissionResponse(BaseModel):
    id: int
    homework_id: int
    owner_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_by: Optional[int] = None
    link: str
    status: HomeworkStatus
    is_late: bool
    is_pass: Optional[bool] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    score_details: Optional[List[ScoreDetail]] = None
    plagiarism_info: Optional[List[dict]] = None
    is_plagiarized: bool = False
    plagiarized_from_user_id: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HomeworkReportResponse(BaseModel):
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    unsubmitted_count: int
