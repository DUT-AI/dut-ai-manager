from datetime import date, datetime

from pydantic import BaseModel

from app.homework.application.dtos import HomeworkResponse
from app.meeting.schemas import MeetingResponse
from app.permission_request.schemas import PermissionRequestResponse
from app.user.application.dtos import UserResponse


class BonusPointResponse(BaseModel):
    id: int
    user_id: int
    points: int
    reason: str
    date: datetime
    user_name: str | None = None
    user_avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ViolationResponse(BaseModel):
    id: int
    user_id: int
    reason: str
    date: datetime
    user_name: str | None = None
    user_avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DailySummaryResponse(BaseModel):
    date: date
    permission_requests: list[PermissionRequestResponse] = []
    bonus_points: list[BonusPointResponse] = []
    violations: list[ViolationResponse] = []
    meetings: list[MeetingResponse] = []


class DashboardOverviewResponse(BaseModel):
    permission_requests: list[PermissionRequestResponse]
    bonus_points: list[BonusPointResponse]
    violations: list[ViolationResponse]
    unsubmitted_homeworks: list[HomeworkResponse]
    meetings: list[MeetingResponse]


class ReportItem(BaseModel):
    rank: int
    user: UserResponse
    total_points: float | None = 0
    total_violations: int | None = 0
    details_count: int


class ReportResponse(BaseModel):
    items: list[ReportItem]
    month: int | None
    year: int | None
