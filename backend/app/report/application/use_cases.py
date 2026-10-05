from datetime import date

from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.homework.application import GetHomeworksUseCase
from app.homework.application.dtos import HomeworkResponse
from app.meeting.infrastructure.repository import MeetingRepository
from app.meeting.schemas import MeetingResponse
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.permission_request.schemas import PermissionRequestResponse
from app.report.schemas import (
    BonusPointResponse,
    DailySummaryResponse,
    DashboardOverviewResponse,
    ReportItem,
    ReportResponse,
    ViolationResponse,
)
from app.user.application.dtos import UserResponse
from app.user.infrastructure.repository import UserRepository
from app.violation.infrastructure.repository import ViolationRepository


class GetDailySummaryUseCase:
    """Tổng hợp hoạt động trong một ngày nhất định"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
        violation_repo: ViolationRepository,
        bonus_point_repo: BonusPointRepository,
    ):
        self.meeting_repo = meeting_repo
        self.permission_repo = permission_repo
        self.violation_repo = violation_repo
        self.bonus_point_repo = bonus_point_repo

    def execute(self, target_date: date) -> DailySummaryResponse:
        # Lấy dữ liệu từ các Repository
        meetings = self.meeting_repo.get_by_date(target_date)
        permissions = self.permission_repo.get_by_date(target_date)
        violations = self.violation_repo.get_by_date(target_date)
        bonus_points = self.bonus_point_repo.get_by_date(target_date)

        return DailySummaryResponse(
            date=target_date,
            meetings=[MeetingResponse.from_domain(m) for m in meetings],
            permission_requests=[
                PermissionRequestResponse.model_validate(p) for p in permissions
            ],
            violations=[ViolationResponse.model_validate(v) for v in violations],
            bonus_points=[BonusPointResponse.model_validate(b) for b in bonus_points],
        )


class GetMonthlyActivityDatesUseCase:
    """Lấy danh sách các ngày có hoạt động trong tháng"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
        violation_repo: ViolationRepository,
        bonus_point_repo: BonusPointRepository,
    ):
        self.meeting_repo = meeting_repo
        self.permission_repo = permission_repo
        self.violation_repo = violation_repo
        self.bonus_point_repo = bonus_point_repo

    def execute(self, month: int, year: int) -> list[date]:
        activity_dates = set()

        # Thống kê từ các nguồn dữ liệu
        # Lưu ý: Các repo cần hỗ trợ phương thức lấy ngày có hoạt động hoặc lấy toàn bộ bản ghi trong tháng

        # 1. Meeting dates
        meetings = self.meeting_repo.get_all_with_participants(
            skip=0, limit=1000, month=month, year=year
        )
        for m in meetings:
            activity_dates.add(m.start_time.date())

        # 2. Permission dates
        permissions = self.permission_repo.get_by_month(
            month=month, year=year, limit=1000
        )
        for p in permissions:
            target_time = getattr(p, "start_time", None) or getattr(
                p, "created_at", None
            )
            if target_time:
                activity_dates.add(
                    target_time.date() if hasattr(target_time, "date") else target_time
                )

        # 3. Violation dates
        violations = self.violation_repo.get_by_month(month=month, year=year)[:1000]
        for v in violations:
            activity_dates.add(v.date.date() if hasattr(v.date, "date") else v.date)

        # 4. BonusPoint dates
        bonus_points = self.bonus_point_repo.get_by_month(month=month, year=year)[:1000]
        for bp in bonus_points:
            activity_dates.add(bp.date.date() if hasattr(bp.date, "date") else bp.date)

        return sorted(activity_dates)


class GetDashboardOverviewUseCase:
    """Thống kê tổng quan cho Dashboard cá nhân của người dùng"""

    def __init__(
        self,
        user_repo: UserRepository,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
        violation_repo: ViolationRepository,
        bonus_point_repo: BonusPointRepository,
        get_homeworks_uc: GetHomeworksUseCase,
    ):
        self.user_repo = user_repo
        self.meeting_repo = meeting_repo
        self.permission_repo = permission_repo
        self.violation_repo = violation_repo
        self.bonus_point_repo = bonus_point_repo
        self.get_homeworks_uc = get_homeworks_uc

    async def execute(
        self, user_id: int, month: int, year: int
    ) -> DashboardOverviewResponse:
        # 1. Permission Requests
        permissions = self.permission_repo.get_by_user(
            user_id=user_id, month=month, year=year
        )

        # 2. Bonus Points
        bonus_points = self.bonus_point_repo.get_by_user_id(
            user_id=user_id, month=month, year=year
        )

        # 3. Violations
        violations = self.violation_repo.get_by_month(
            user_id=user_id, month=month, year=year
        )

        # 4. Assigned Homework (Lấy các bài tập chưa nộp tính đến tháng được chọn)
        user_unsubmitted = await self.get_homeworks_uc.get_unsubmitted_for_user(user_id)
        month_unsubmitted = [
            h
            for h in user_unsubmitted
            if not h.deadline
            or (
                h.deadline.year < year
                or (h.deadline.year == year and h.deadline.month <= month)
            )
        ]

        # 5. Meetings (Lấy các buổi sinh hoạt mà user tham gia trong tháng)
        user_meetings = self.meeting_repo.get_participating_meetings(
            user_id=user_id, month=month, year=year
        )

        return DashboardOverviewResponse(
            permission_requests=[
                PermissionRequestResponse.model_validate(p) for p in permissions
            ],
            bonus_points=[BonusPointResponse.model_validate(b) for b in bonus_points],
            violations=[ViolationResponse.model_validate(v) for v in violations],
            unsubmitted_homeworks=[
                HomeworkResponse.model_validate(h) for h in month_unsubmitted
            ],
            meetings=[MeetingResponse.from_domain(m) for m in user_meetings],
        )


class GetBonusPointReportUseCase:
    """Báo cáo xếp hạng điểm cộng trong tháng (delegated query xuống Repository)."""

    def __init__(
        self,
        bonus_point_repo: BonusPointRepository,
    ):
        self.bonus_point_repo = bonus_point_repo

    def execute(
        self,
        month: int | None = None,
        year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        keyword: str | None = None,
    ) -> ReportResponse:
        rows = self.bonus_point_repo.get_aggregated_report(
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
            keyword=keyword,
        )

        report_items = [
            ReportItem(
                rank=idx + 1,
                user=UserResponse(
                    id=r["user_id"],
                    name=r["name"],
                    email=r["email"],
                    avatar_url=r["avatar_url"],
                    status=r["status"],
                    phone_number=r["phone_number"],
                ),
                total_points=float(r["total_points"] or 0),
                total_violations=0,
                details_count=int(r["details_count"] or 0),
            )
            for idx, r in enumerate(rows)
        ]

        return ReportResponse(items=report_items, month=month, year=year)


class GetViolationReportUseCase:
    """Báo cáo xếp hạng vi phạm trong tháng (delegated query xuống Repository)."""

    def __init__(
        self,
        violation_repo: ViolationRepository,
    ):
        self.violation_repo = violation_repo

    def execute(
        self,
        month: int | None = None,
        year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        keyword: str | None = None,
    ) -> ReportResponse:
        rows = self.violation_repo.get_aggregated_report(
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
            keyword=keyword,
        )

        report_items = [
            ReportItem(
                rank=idx + 1,
                user=UserResponse(
                    id=r["user_id"],
                    name=r["name"],
                    email=r["email"],
                    avatar_url=r["avatar_url"],
                    status=r["status"],
                    phone_number=r["phone_number"],
                ),
                total_points=0,
                total_violations=int(r["total_violations"] or 0),
                details_count=int(r["details_count"] or 0),
            )
            for idx, r in enumerate(rows)
        ]

        return ReportResponse(items=report_items, month=month, year=year)
