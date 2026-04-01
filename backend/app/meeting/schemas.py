from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .domain.value_objects import ParticipantStatus


class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    check_in_at: Optional[datetime] = None
    status: ParticipantStatus
    link_image: Optional[str] = None


class MeetingCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: Optional[str] = Field(None, max_length=1000)
    start_time: datetime
    end_time: datetime
    require_check_in: bool = True
    user_ids: List[int] = []
    team_ids: List[int] = []


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, max_length=1000)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    require_check_in: Optional[bool] = None
    user_ids: Optional[List[int]] = None
    team_ids: Optional[List[int]] = None


class MeetingResponse(BaseModel):
    id: int
    title: str
    content: Optional[str]
    start_time: datetime
    end_time: datetime
    require_check_in: bool
    participants: List[ParticipantResponse] = []
    created_at: datetime
    updated_at: datetime
