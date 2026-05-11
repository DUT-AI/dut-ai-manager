from typing import List, Optional
from app.user.domain.monthly_stats import UserTitle
from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
from app.user.infrastructure.repository import UserRepository
from app.user.application.dtos import UserResponse
from pydantic import BaseModel


class TitleReportItem(BaseModel):
    user: UserResponse
    title: Optional[str]
    total_points: int
    violation_count: int
    hours: float


class GetCurrentTitleUseCase:
    """Lấy danh hiệu hiện tại của user"""

    def __init__(self, stats_repo: MonthlyUserStatsRepository):
        self.stats_repo = stats_repo

    def execute(self, user_id: int) -> Optional[str]:
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

    def execute(self, month: int, year: int) -> List[TitleReportItem]:
        stats_list = self.stats_repo.get_by_month_year(month, year)

        report_items = []
        for stats in stats_list:
            user = self.user_repo.get_by_id(stats.user_id)
            if not user:
                continue
            report_items.append(
                TitleReportItem(
                    user=UserResponse.model_validate(user),
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
