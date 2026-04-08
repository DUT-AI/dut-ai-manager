from datetime import datetime
from typing import Optional

from app.permission_request.domain.value_objects import RequestCategory
from pydantic import BaseModel, ConfigDict

from app.user.application.dtos import UserResponse
from app.homework.application.dtos import HomeworkResponse
from app.meeting.schemas import MeetingResponse


class PermissionRequestBase(BaseModel):
    category: RequestCategory
    note: str
    homework_id: Optional[int] = None
    meeting_id: Optional[int] = None
    start_time: Optional[datetime] = None


class PermissionRequestCreate(PermissionRequestBase):
    pass


class PermissionRequestUpdate(BaseModel):
    category: Optional[RequestCategory] = None
    note: Optional[str] = None
    homework_id: Optional[int] = None
    meeting_id: Optional[int] = None
    start_time: Optional[datetime] = None


class PermissionRequestResponse(PermissionRequestBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    # Related objects
    user: Optional[UserResponse] = None
    homework: Optional[HomeworkResponse] = None
    meeting: Optional[MeetingResponse] = None

    model_config = ConfigDict(from_attributes=True)
