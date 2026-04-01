from datetime import date, datetime
from typing import List, Optional

from app.homework.application.dtos import HomeworkResponse
from app.meeting.schemas import MeetingResponse
from app.permission_request.schemas import PermissionRequestResponse
from app.user.application.dtos import UserResponse
from pydantic import BaseModel


class BonusPointResponse(BaseModel):
    id: int
    user_id: int
    points: int
    reason: str
    date: datetime
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ViolationResponse(BaseModel):
    id: int
    user_id: int
    reason: str
    date: datetime
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
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


class DashboardOverviewResponse(BaseModel):
    permission_requests: List[PermissionRequestResponse]
    bonus_points: List[BonusPointResponse]
    violations: List[ViolationResponse]
    unsubmitted_homeworks: List[HomeworkResponse]
    meetings: List[MeetingResponse]


class ReportItem(BaseModel):
    rank: int
    user: UserResponse
    total_points: Optional[float] = 0
    total_violations: Optional[int] = 0
    details_count: int


class ReportResponse(BaseModel):
    items: List[ReportItem]
    month: Optional[int]
    year: Optional[int]
