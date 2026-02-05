from typing import List, Optional
from pydantic import BaseModel

from app.schemas.activity import BonusPointResponse, ViolationResponse
from app.schemas.homework import HomeworkResponse
from app.schemas.meeting import MeetingResponse
from app.schemas.permission_request import PermissionRequestResponse
from app.schemas.user import UserResponse


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
