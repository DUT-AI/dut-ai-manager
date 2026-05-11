from typing import Optional
from app.shared.infrastructure.base_model import TimestampMixin
from app.user.domain.monthly_stats import MonthlyUserStats, UserTitle
from sqlmodel import Field, UniqueConstraint


class MonthlyUserStatsModel(TimestampMixin, table=True):
    """ORM model for monthly user statistics and titles"""
    __tablename__ = "monthly_user_stats"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    month: int
    year: int

    total_activity_hours: float = Field(default=0)
    total_bonus_points: int = Field(default=0)
    late_count: int = Field(default=0)
    absent_count: int = Field(default=0)
    violation_count: int = Field(default=0)

    assigned_title: Optional[str] = Field(default=None, max_length=50)

    __table_args__ = (
        UniqueConstraint("user_id", "month", "year"),
    )

    def to_entity(self) -> MonthlyUserStats:
        return MonthlyUserStats(
            id=self.id,
            user_id=self.user_id,
            month=self.month,
            year=self.year,
            total_activity_hours=self.total_activity_hours,
            total_bonus_points=self.total_bonus_points,
            late_count=self.late_count,
            absent_count=self.absent_count,
            violation_count=self.violation_count,
            assigned_title=UserTitle(self.assigned_title) if self.assigned_title else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )
