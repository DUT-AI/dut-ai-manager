from datetime import date, datetime
from typing import List, Optional

from app.schemas.meeting import MeetingResponse
from app.schemas.permission_request import PermissionRequestResponse
from pydantic import BaseModel


class BonusPointBase(BaseModel):
    points: int
    reason: str
    date: datetime


class BonusPointCreate(BonusPointBase):
    user_id: int


class BonusPointUpdate(BaseModel):
    points: Optional[int] = None
    reason: Optional[str] = None
    date: Optional[datetime] = None


class BonusPointResponse(BonusPointBase):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    creator_name: Optional[str] = None
    updater_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ViolationBase(BaseModel):
    reason: str
    date: datetime


class ViolationCreate(ViolationBase):
    user_id: int


class ViolationUpdate(BaseModel):
    reason: Optional[str] = None
    date: Optional[datetime] = None


class ViolationResponse(ViolationBase):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    creator_name: Optional[str] = None
    updater_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DailySummaryResponse(BaseModel):
    date: date
    permission_requests: List[PermissionRequestResponse] = []
    bonus_points: List[BonusPointResponse] = []
    violations: List[ViolationResponse] = []
    meetings: List[MeetingResponse] = []
