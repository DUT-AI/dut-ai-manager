from dishka import Provider, Scope, provide
from app.report.application.use_cases import (
    GetDailySummaryUseCase,
    GetMonthlyActivityDatesUseCase,
    GetDashboardOverviewUseCase,
    GetBonusPointReportUseCase,
    GetViolationReportUseCase,
)
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.violation.infrastructure.repository import ViolationRepository
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.user.infrastructure.repository import UserRepository
from app.homework.infrastructure.repository import HomeworkSubmissionRepository

class ReportModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_daily_summary_uc(
        self,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
        violation_repo: ViolationRepository,
        bonus_point_repo: BonusPointRepository,
    ) -> GetDailySummaryUseCase:
        return GetDailySummaryUseCase(
            meeting_repo, permission_repo, violation_repo, bonus_point_repo
        )

    @provide
    def get_monthly_activity_dates_uc(
        self,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
        violation_repo: ViolationRepository,
        bonus_point_repo: BonusPointRepository,
    ) -> GetMonthlyActivityDatesUseCase:
        return GetMonthlyActivityDatesUseCase(
            meeting_repo, permission_repo, violation_repo, bonus_point_repo
        )

    @provide
    def get_dashboard_overview_uc(
        self,
        user_repo: UserRepository,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
        violation_repo: ViolationRepository,
        bonus_point_repo: BonusPointRepository,
        submission_repo: HomeworkSubmissionRepository,
    ) -> GetDashboardOverviewUseCase:
        return GetDashboardOverviewUseCase(
            user_repo,
            meeting_repo,
            permission_repo,
            violation_repo,
            bonus_point_repo,
            submission_repo,
        )

    @provide
    def get_bonus_point_report_uc(
        self, bonus_point_repo: BonusPointRepository, user_repo: UserRepository
    ) -> GetBonusPointReportUseCase:
        return GetBonusPointReportUseCase(bonus_point_repo, user_repo)

    @provide
    def get_violation_report_uc(
        self, violation_repo: ViolationRepository, user_repo: UserRepository
    ) -> GetViolationReportUseCase:
        return GetViolationReportUseCase(violation_repo, user_repo)
