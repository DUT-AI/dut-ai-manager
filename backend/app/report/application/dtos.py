from datetime import date

from pydantic import BaseModel

from app.bonus_point.application.dtos import BonusPointResponse
from app.homework.application.dtos import HomeworkResponse
from app.meeting.schemas import MeetingResponse
from app.permission_request.schemas import PermissionRequestResponse
from app.user.application.dtos import UserResponse
from app.violation.schemas import ViolationResponse


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
    total_points: float = 0
    total_violations: int = 0
    details_count: int


class ReportResponse(BaseModel):
    items: list[ReportItem]
    month: int | None
    year: int | None
