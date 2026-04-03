from datetime import date
from typing import List, Optional

from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.homework.application.dtos import HomeworkResponse
from app.homework.infrastructure.repository import HomeworkSubmissionRepository
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

    def execute(self, month: int, year: int) -> List[date]:
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
            activity_dates.add(p.date)

        # 3. Violation dates
        violations = self.violation_repo.get_by_month(month=month, year=year)[:1000]
        for v in violations:
            activity_dates.add(v.date.date() if hasattr(v.date, "date") else v.date)

        # 4. BonusPoint dates
        bonus_points = self.bonus_point_repo.get_by_month(month=month, year=year)[:1000]
        for bp in bonus_points:
            activity_dates.add(bp.date.date() if hasattr(bp.date, "date") else bp.date)

        return sorted(list(activity_dates))


class GetDashboardOverviewUseCase:
    """Thống kê tổng quan cho Dashboard cá nhân của người dùng"""

    def __init__(
        self,
        user_repo: UserRepository,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
        violation_repo: ViolationRepository,
        bonus_point_repo: BonusPointRepository,
        submission_repo: HomeworkSubmissionRepository,
    ):
        self.user_repo = user_repo
        self.meeting_repo = meeting_repo
        self.permission_repo = permission_repo
        self.violation_repo = violation_repo
        self.bonus_point_repo = bonus_point_repo
        self.submission_repo = submission_repo

    def execute(self, user_id: int, month: int, year: int) -> DashboardOverviewResponse:
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

        # 4. Unsubmitted Homework (Lấy thực thể bài tập chưa nộp)
        unsubmitted_homeworks = self.submission_repo.get_all_by_user(user_id)
        # Lấy list HomeworkEntities từ submissions (giả sử submission entity có field homework)
        homework_entities = [s.homework for s in unsubmitted_homeworks if hasattr(s, "homework") and s.homework]

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
                HomeworkResponse.model_validate(h) for h in homework_entities
            ],
            meetings=[MeetingResponse.from_domain(m) for m in user_meetings],
        )


class GetBonusPointReportUseCase:
    """Báo cáo xếp hạng điểm cộng trong tháng"""

    def __init__(
        self,
        bonus_point_repo: BonusPointRepository,
        user_repo: UserRepository,
    ):
        self.bonus_point_repo = bonus_point_repo
        self.user_repo = user_repo

    def execute(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> ReportResponse:
        records = self.bonus_point_repo.get_by_month(month=month, year=year)[:2000]

        user_stats: dict = {}
        for record in records:
            if not record.owner:
                continue

            if keyword and keyword.lower() not in record.owner.name.lower():
                continue

            u_id = record.user_id
            if u_id not in user_stats:
                user_stats[u_id] = {
                    "user_id": u_id,
                    "total_points": 0,
                    "count": 0,
                }

            user_stats[u_id]["total_points"] += record.points
            user_stats[u_id]["count"] += 1

        sorted_items = sorted(
            user_stats.values(), key=lambda x: x["total_points"], reverse=True
        )

        report_items = []
        for idx, item in enumerate(sorted_items):
            user_entity = self.user_repo.get_by_id(item["user_id"])
            if not user_entity:
                continue
            report_items.append(
                ReportItem(
                    rank=idx + 1,
                    user=UserResponse.model_validate(user_entity),
                    total_points=float(item["total_points"]),
                    total_violations=0,
                    details_count=item["count"],
                )
            )

        return ReportResponse(items=report_items, month=month, year=year)


class GetViolationReportUseCase:
    """Báo cáo xếp hạng vi phạm trong tháng"""

    def __init__(
        self,
        violation_repo: ViolationRepository,
        user_repo: UserRepository,
    ):
        self.violation_repo = violation_repo
        self.user_repo = user_repo

    def execute(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> ReportResponse:
        records = self.violation_repo.get_by_month(month=month, year=year)[:2000]

        user_stats: dict = {}
        for record in records:
            if not record.owner:
                continue

            if keyword and keyword.lower() not in record.owner.name.lower():
                continue

            u_id = record.user_id
            if u_id not in user_stats:
                user_stats[u_id] = {
                    "user_id": u_id,
                    "total_violations": 0,
                    "count": 0,
                }

            user_stats[u_id]["total_violations"] += 1
            user_stats[u_id]["count"] += 1

        sorted_items = sorted(
            user_stats.values(), key=lambda x: x["total_violations"], reverse=True
        )

        report_items = []
        for idx, item in enumerate(sorted_items):
            user_entity = self.user_repo.get_by_id(item["user_id"])
            if not user_entity:
                continue
            report_items.append(
                ReportItem(
                    rank=idx + 1,
                    user=UserResponse.model_validate(user_entity),
                    total_points=0,
                    total_violations=item["total_violations"],
                    details_count=item["count"],
                )
            )

        return ReportResponse(items=report_items, month=month, year=year)
