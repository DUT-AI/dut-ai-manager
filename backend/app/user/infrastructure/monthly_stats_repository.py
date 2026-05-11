from datetime import date, timedelta
from typing import List, Optional
from app.shared.infrastructure.base_repository import BaseRepository
from app.user.domain.monthly_stats import MonthlyUserStats
from app.user.infrastructure.monthly_stats_model import MonthlyUserStatsModel
from sqlmodel import Session, select


class MonthlyUserStatsRepository(BaseRepository[MonthlyUserStatsModel, MonthlyUserStats]):
    def __init__(self, session: Session):
        super().__init__(session, MonthlyUserStatsModel)

    def to_entity(self, model: MonthlyUserStatsModel) -> MonthlyUserStats:
        return model.to_entity()

    def from_entity(self, entity: MonthlyUserStats) -> MonthlyUserStatsModel:
        return MonthlyUserStatsModel(
            id=entity.id,
            user_id=entity.user_id,
            month=entity.month,
            year=entity.year,
            total_activity_hours=entity.total_activity_hours,
            total_bonus_points=entity.total_bonus_points,
            late_count=entity.late_count,
            absent_count=entity.absent_count,
            violation_count=entity.violation_count,
            assigned_title=entity.assigned_title.value if entity.assigned_title else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )

    def get_by_user_and_month(
        self, user_id: int, month: int, year: int
    ) -> Optional[MonthlyUserStats]:
        stmt = select(MonthlyUserStatsModel).where(
            MonthlyUserStatsModel.user_id == user_id,
            MonthlyUserStatsModel.month == month,
            MonthlyUserStatsModel.year == year,
        )
        model = self.session.exec(stmt).first()
        return self.to_entity(model) if model else None

    def get_by_month_year(self, month: int, year: int) -> List[MonthlyUserStats]:
        stmt = (
            select(MonthlyUserStatsModel)
            .where(
                MonthlyUserStatsModel.month == month,
                MonthlyUserStatsModel.year == year,
            )
            .order_by(MonthlyUserStatsModel.total_bonus_points.desc())
        )
        models = self.session.exec(stmt).all()
        return [self.to_entity(m) for m in models]

    def get_current_title(self, user_id: int) -> Optional[str]:
        """Lấy danh hiệu hiện tại (xét tháng trước, áp dụng tháng này)."""
        from app.utils.datetime import get_current_utc7_time
        now = get_current_utc7_time()

        # Lấy danh hiệu của tháng trước
        first_day = now.replace(day=1)
        last_month = first_day - timedelta(days=1)

        stats = self.get_by_user_and_month(
            user_id, last_month.month, last_month.year
        )
        return stats.assigned_title.value if stats and stats.assigned_title else None

    def save(self, entity: MonthlyUserStats) -> MonthlyUserStats:
        """Upsert monthly stats"""
        existing = self.get_by_user_and_month(entity.user_id, entity.month, entity.year)
        if existing and existing.id:
            # Update
            model = self.session.get(MonthlyUserStatsModel, existing.id)
            model.total_activity_hours = entity.total_activity_hours
            model.total_bonus_points = entity.total_bonus_points
            model.late_count = entity.late_count
            model.absent_count = entity.absent_count
            model.violation_count = entity.violation_count
            model.assigned_title = entity.assigned_title.value if entity.assigned_title else None
            self.session.add(model)
            self.session.flush()
            return self.to_entity(model)
        else:
            # Insert
            model = self.from_entity(entity)
            self.session.add(model)
            self.session.flush()
            return self.to_entity(model)
