from datetime import date
from typing import List

from pydantic import BaseModel


class DailySummaryResponse(BaseModel):
    date: date
    permission_requests: List[PermissionRequestResponse] = []
    bonus_points: List[BonusPointResponse] = []
    violations: List[ViolationResponse] = []
    meetings: List[MeetingResponse] = []
