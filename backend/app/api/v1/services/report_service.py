from datetime import date
from typing import List

from app.api.v1.services.bonus_point_service import BonusPointService
from app.api.v1.services.violation_service import ViolationService
from app.api.v1.services.meeting_service import MeetingService
from app.api.v1.services.permission_request_service import PermissionRequestService
from app.schemas.activity import (
    BonusPointResponse,
    DailySummaryResponse,
    ViolationResponse,
)
from app.schemas.meeting import MeetingResponse
from app.schemas.permission_request import PermissionRequestResponse


class ReportService:
    """Service for Report operations - uses existing services"""

    def __init__(
        self,
        bonus_point_service: BonusPointService,
        violation_service: ViolationService,
        permission_request_service: PermissionRequestService,
        meeting_service: MeetingService,
    ):
        self.bonus_point_service = bonus_point_service
        self.violation_service = violation_service
        self.permission_request_service = permission_request_service
        self.meeting_service = meeting_service

    def get_daily_summary(self, target_date: date) -> DailySummaryResponse:
        """Get daily summary of all activities"""
        permission_requests = self.permission_request_service.get_by_date(target_date)
        bonus_points = self.bonus_point_service.get_by_date(target_date)
        violations = self.violation_service.get_by_date(target_date)
        meetings = self.meeting_service.get_by_date(target_date)

        return DailySummaryResponse(
            date=target_date,
            permission_requests=[
                PermissionRequestResponse.model_validate(r) for r in permission_requests
            ],
            bonus_points=[BonusPointResponse.model_validate(b) for b in bonus_points],
            violations=[ViolationResponse.model_validate(v) for v in violations],
            meetings=[MeetingResponse.model_validate(m) for m in meetings],
        )

    def get_monthly_activity_dates(self, month: int, year: int) -> List[date]:
        """Get all dates with any activity in the given month for all users"""
        # Use existing services with month/year filter (fetching all users)
        bonus_points = self.bonus_point_service.get(month=month, year=year)
        violations = self.violation_service.get(month=month, year=year)
        permissions = self.permission_request_service.get(month=month, year=year)

        activity_dates = set()

        for bp in bonus_points:
            if bp.date:
                activity_dates.add(
                    bp.date.date() if hasattr(bp.date, "date") else bp.date
                )

        for v in violations:
            if v.date:
                activity_dates.add(v.date.date() if hasattr(v.date, "date") else v.date)

        for p in permissions:
            if p.date:
                activity_dates.add(p.date)

        meetings = self.meeting_service.get_all(limit=1000)  # Simple approach for now
        # Ideally, MeetingService should have a get() with month/year filter too
        for m in meetings:
            if m.start_time.month == month and m.start_time.year == year:
                activity_dates.add(m.start_time.date())

        return sorted(list(activity_dates))
