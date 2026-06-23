from datetime import timedelta

from loguru import logger
from pydantic import BaseModel

from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.shared.application.response import UserInfoResponse
from app.user.domain.monthly_stats import MonthlyUserStats
from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time
from app.violation.infrastructure.repository import ViolationRepository
from app.violation.domain.entity import ViolationType
from app.report.application.participation_use_cases import GetParticipationAnalysisUseCase


class TitleReportItem(BaseModel):
    user: UserInfoResponse
    title: str | None
    total_points: int
    violation_count: int
    hours: float


class GetCurrentTitleUseCase:
    """Lấy danh hiệu hiện tại của user"""

    def __init__(self, stats_repo: MonthlyUserStatsRepository):
        self.stats_repo = stats_repo

    def execute(self, user_id: int) -> str | None:
        return self.stats_repo.get_current_title(user_id)


class GetMonthlyTitlesReportUseCase:
    """Lấy bảng danh hiệu tháng"""

    def __init__(
        self,
        stats_repo: MonthlyUserStatsRepository,
        user_repo: UserRepository,
    ):
        self.stats_repo = stats_repo
        self.user_repo = user_repo

    def execute(self, month: int, year: int) -> list[TitleReportItem]:
        stats_list = self.stats_repo.get_by_month_year(month, year)

        report_items = []
        for stats in stats_list:
            user = self.user_repo.get_by_id(stats.user_id)
            if not user:
                continue
            report_items.append(
                TitleReportItem(
                    user=UserInfoResponse(**user.model_dump()),
                    title=stats.assigned_title.value if stats.assigned_title else None,
                    total_points=stats.total_bonus_points,
                    violation_count=stats.violation_count,
                    hours=stats.total_activity_hours,
                )
            )

        # Sắp xếp: Tích cực trước, rồi Bình thường, Hoạt động kém cuối
        title_order = {"Tích cực": 0, "Bình thường": 1, "Hoạt động kém": 2}
        report_items.sort(
            key=lambda x: title_order.get(x.title or "", 99), reverse=False
        )

        return report_items


class AssignMonthlyTitlesUseCase:
    """Xét danh hiệu cho tháng target và lưu vào DB."""

    def __init__(
        self,
        stats_repo: MonthlyUserStatsRepository,
        bonus_repo: BonusPointRepository,
        violation_repo: ViolationRepository,
        user_repo: UserRepository,
        analysis_uc: GetParticipationAnalysisUseCase,
    ):
        self.stats_repo = stats_repo
        self.bonus_repo = bonus_repo
        self.violation_repo = violation_repo
        self.user_repo = user_repo
        self.analysis_uc = analysis_uc

    def execute(
        self,
        target_month: int | None = None,
        target_year: int | None = None,
    ) -> int:

        now = get_current_utc7_time()

        if target_month is None or target_year is None:
            first_day_of_month = now.replace(day=1)
            last_month = first_day_of_month - timedelta(days=1)
            target_month = last_month.month
            target_year = last_month.year

        users = self.user_repo.get_active_users()
        count = 0
        for user in users:
            assert user.id is not None
            try:
                violations = self.violation_repo.get_by_month(
                    user.id, target_month, target_year
                )
                
                late_count = sum(1 for v in violations if v.type == ViolationType.LATE)
                absent_count = sum(1 for v in violations if v.type == ViolationType.ABSENT)
                violation_count = late_count + absent_count

                # Lấy số giờ hoạt động để tính điểm cộng
                analysis = self.analysis_uc.execute(user.id, target_month, target_year)
                total_hours = analysis.total_hours
                attendance_bonus = int(total_hours) # Cứ 60 phút hoạt động liên tục được 1 điểm
                
                stats = MonthlyUserStats(
                    user_id=user.id,
                    month=target_month,
                    year=target_year,
                    total_activity_hours=total_hours,
                    total_bonus_points=attendance_bonus,
                    late_count=late_count,
                    absent_count=absent_count,
                    violation_count=violation_count,
                )

                title = stats.calculate_title()
                stats.assigned_title = title

                self.stats_repo.save(stats)
                count += 1

            except Exception as e:
                logger.error(f"❌ Failed to assign title for user {user.id}: {e}")

        return count
