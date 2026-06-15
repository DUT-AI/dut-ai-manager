from dishka import Provider, Scope, provide

from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.homework.infrastructure.repository import HomeworkSubmissionRepository
from app.meeting.infrastructure.repository import MeetingRepository, ParticipantRepository
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.report.application.title_use_cases import (
    AssignMonthlyTitlesUseCase,
    GetCurrentTitleUseCase,
    GetMonthlyTitlesReportUseCase,
)
from app.report.application.participation_use_cases import (
    GetParticipationAnalysisUseCase,
    GetParticipationLeaderboardUseCase,
)
from app.report.application.trend_use_cases import GetActivityTrendUseCase
from app.report.application.use_cases import (
    GetBonusPointReportUseCase,
    GetDailySummaryUseCase,
    GetDashboardOverviewUseCase,
    GetMonthlyActivityDatesUseCase,
    GetViolationReportUseCase,
)
from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
from app.user.infrastructure.repository import UserRepository
from app.violation.infrastructure.repository import ViolationRepository


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

    @provide
    def get_current_title_uc(
        self, stats_repo: MonthlyUserStatsRepository
    ) -> GetCurrentTitleUseCase:
        return GetCurrentTitleUseCase(stats_repo)

    @provide
    def get_monthly_titles_report_uc(
        self,
        stats_repo: MonthlyUserStatsRepository,
        user_repo: UserRepository,
    ) -> GetMonthlyTitlesReportUseCase:
        return GetMonthlyTitlesReportUseCase(stats_repo, user_repo)

    @provide
    def get_assign_monthly_titles_uc(
        self,
        stats_repo: MonthlyUserStatsRepository,
        bonus_repo: BonusPointRepository,
        violation_repo: ViolationRepository,
        user_repo: UserRepository,
        analysis_uc: GetParticipationAnalysisUseCase,
    ) -> AssignMonthlyTitlesUseCase:
        return AssignMonthlyTitlesUseCase(
            stats_repo, bonus_repo, violation_repo, user_repo, analysis_uc
        )

    @provide
    def get_participation_analysis_uc(
        self,
        participant_repo: ParticipantRepository,
        violation_repo: ViolationRepository,
    ) -> GetParticipationAnalysisUseCase:
        return GetParticipationAnalysisUseCase(participant_repo, violation_repo)

    @provide
    def get_participation_leaderboard_uc(
        self,
        user_repo: UserRepository,
        stats_repo: MonthlyUserStatsRepository,
        analysis_uc: GetParticipationAnalysisUseCase,
    ) -> GetParticipationLeaderboardUseCase:
        return GetParticipationLeaderboardUseCase(user_repo, stats_repo, analysis_uc)

    @provide
    def get_activity_trend_uc(
        self,
        bonus_point_repo: BonusPointRepository,
        violation_repo: ViolationRepository,
        participant_repo: ParticipantRepository,
    ) -> GetActivityTrendUseCase:
        return GetActivityTrendUseCase(bonus_point_repo, violation_repo, participant_repo)
