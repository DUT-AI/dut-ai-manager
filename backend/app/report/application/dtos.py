from datetime import date
from typing import List

from pydantic import BaseModel
from typing import List, Optional

from app.meeting.schemas import MeetingResponse
from app.bonus_point.application.dtos import BonusPointResponse
from app.homework.application.dtos import HomeworkResponse
from app.permission_request.application.dtos import PermissionRequestResponse
from app.user.application.dtos import UserResponse


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
