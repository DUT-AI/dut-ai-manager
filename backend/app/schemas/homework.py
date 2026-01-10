from datetime import datetime
from typing import List, Optional

from app.models import HomeworkStatus
from pydantic import BaseModel, HttpUrl


class HomeworkBase(BaseModel):
    title: str
    description: str
    deadline: datetime


class HomeworkCreate(HomeworkBase):
    assignee_ids: Optional[List[int]]


class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    assignee_ids: Optional[List[int]] = None


class HomeworkResponse(HomeworkBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    # Computed fields (can be populated by service/repo)
    assignee_count: int = 0
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
    user_name: Optional[str] = None
    created_by: Optional[int] = None
    link: str
    status: HomeworkStatus
    is_late: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
