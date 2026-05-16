from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.homework.application.dtos import HomeworkResponse
from app.meeting.schemas import MeetingResponse
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.value_objects import UserRef


class PermissionRequestBase(BaseModel):
    category: RequestCategory
    note: str
    homework_id: int | None = None
    meeting_id: int | None = None
    start_time: datetime | None = None


class PermissionRequestCreate(PermissionRequestBase):
    pass


class PermissionRequestUpdate(BaseModel):
    category: RequestCategory | None = None
    note: str | None = None
    homework_id: int | None = None
    meeting_id: int | None = None
    start_time: datetime | None = None


class PermissionRequestResponse(PermissionRequestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Related objects
    owner: UserRef | None = None
    creator: UserRef | None = None
    updater: UserRef | None = None
    homework: HomeworkResponse | None = None
    meeting: MeetingResponse | None = None

    model_config = ConfigDict(from_attributes=True)
