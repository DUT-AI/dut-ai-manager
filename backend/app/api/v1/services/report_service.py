from typing import Optional
from app.schemas.homework import HomeworkResponse
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
        homework_submission_service: "HomeworkSubmissionService",  # Type hint string to avoid circular import if needed
    ):
        self.bonus_point_service = bonus_point_service
        self.violation_service = violation_service
        self.permission_request_service = permission_request_service
        self.meeting_service = meeting_service
        self.homework_submission_service = homework_submission_service

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
        """Get all dates with all activity in the given month for all users"""
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

        meetings = self.meeting_service.get_all(limit=1000, month=month, year=year)
        for m in meetings:
            activity_dates.add(m.start_time.date())

        return sorted(list(activity_dates))

    def get_dashboard_overview(
        self, user_id: int, month: int, year: int
    ) -> "DashboardOverviewResponse":
        """Get dashboard overview for a specific user and month"""
        from app.schemas.report import DashboardOverviewResponse
        from app.models.homework_submission import HomeworkStatus

        # 1. Permission Requests
        permissions = self.permission_request_service.get_by_user(
            user_id=user_id, month=month, year=year
        )

        # 2. Bonus Points
        bonus_points = self.bonus_point_service.get(
            month=month, year=year, user_id=user_id
        )

        # 3. Violations
        violations = self.violation_service.get(month=month, year=year, user_id=user_id)

        # 4. Unsubmitted Homework
        unsubmitted_homeworks = (
            self.homework_submission_service.get_unsubmitted_by_user(user_id)
        )

        # 5. Meetings (Participating, in month)
        user_meetings = self.meeting_service.get_participating_meetings(
            user_id=user_id, month=month, year=year
        )

        return DashboardOverviewResponse(
            permission_requests=[
                PermissionRequestResponse.model_validate(p) for p in permissions
            ],
            bonus_points=[BonusPointResponse.model_validate(b) for b in bonus_points],
            violations=[ViolationResponse.model_validate(v) for v in violations],
            unsubmitted_homeworks=[
                HomeworkResponse.model_validate(h) for h in unsubmitted_homeworks
            ],
            meetings=[MeetingResponse.model_validate(m) for m in user_meetings],
        )

    def get_bonus_point_report(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> "ReportResponse":
        """Get aggregated bonus point report"""
        from app.schemas.report import ReportResponse, ReportItem
        from app.schemas.user import UserResponse

        # Fetch all records (potentially filtered by month/year)
        records = self.bonus_point_service.get(month=month, year=year)

        # Aggregate by User
        user_stats = {}
        for record in records:
            if not record.user:
                continue

            # Search filter
            if keyword and keyword.lower() not in record.user.name.lower():
                continue

            user_id = record.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "user": record.user,
                    "total_points": 0,
                    "count": 0,
                }

            user_stats[user_id]["total_points"] += record.points
            user_stats[user_id]["count"] += 1

        # Convert to list and sort
        sorted_items = sorted(
            user_stats.values(), key=lambda x: x["total_points"], reverse=True
        )

        # Build response with rank
        report_items = []
        for idx, item in enumerate(sorted_items):
            report_items.append(
                ReportItem(
                    rank=idx + 1,
                    user=UserResponse.model_validate(item["user"]),
                    total_points=item["total_points"],
                    total_violations=0,
                    details_count=item["count"],
                )
            )

        return ReportResponse(items=report_items, month=month, year=year)

    def get_violation_report(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> "ReportResponse":
        """Get aggregated violation report"""
        from app.schemas.report import ReportResponse, ReportItem
        from app.schemas.user import UserResponse

        # Fetch all records
        records = self.violation_service.get(month=month, year=year)

        # Aggregate by User
        user_stats = {}
        for record in records:
            if not record.user:
                continue

            # Search filter
            if keyword and keyword.lower() not in record.user.name.lower():
                continue

            user_id = record.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "user": record.user,
                    "total_violations": 0,
                    "count": 0,
                }

            # Count violations (assuming 1 record = 1 violation count, or check logic if strict needed)
            # Typically violation records count as 1 occurrence
            user_stats[user_id]["total_violations"] += 1
            user_stats[user_id]["count"] += 1

        # Convert to list and sort
        sorted_items = sorted(
            user_stats.values(), key=lambda x: x["total_violations"], reverse=True
        )

        # Build response with rank
        report_items = []
        for idx, item in enumerate(sorted_items):
            report_items.append(
                ReportItem(
                    rank=idx + 1,
                    user=UserResponse.model_validate(item["user"]),
                    total_points=0,
                    total_violations=item["total_violations"],
                    details_count=item["count"],
                )
            )

        return ReportResponse(items=report_items, month=month, year=year)
