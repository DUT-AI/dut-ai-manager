from datetime import datetime
from typing import List, Optional

from app.models.meeting import ParticipantStatus
from pydantic import BaseModel


class MeetingBase(BaseModel):
    title: str
    content: Optional[str] = None
    start_time: datetime
    end_time: datetime
    require_check_in: bool = True


class MeetingCreate(MeetingBase):
    team_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    require_check_in: Optional[bool] = None
    team_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None


class ParticipantResponse(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    check_in_at: Optional[datetime] = None
    status: ParticipantStatus
    link_image: Optional[str] = None

    class Config:
        from_attributes = True


class MeetingResponse(MeetingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    participants: List[ParticipantResponse] = []

    class Config:
        from_attributes = True


class MeetingCheckIn(BaseModel):
    meeting_id: int
    user_id: int
