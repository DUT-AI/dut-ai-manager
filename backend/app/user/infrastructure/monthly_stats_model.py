from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.user.domain.monthly_stats import MonthlyUserStats, UserTitle


class MonthlyUserStatsModel(SQLAlchemyTimestampMixin, Base):
    """ORM model for monthly user statistics and titles"""

    __tablename__ = "monthly_user_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    month: Mapped[int]
    year: Mapped[int]

    total_activity_hours: Mapped[float] = mapped_column(Float, default=0.0)
    total_bonus_points: Mapped[int] = mapped_column(Integer, default=0)
    late_count: Mapped[int] = mapped_column(Integer, default=0)
    absent_count: Mapped[int] = mapped_column(Integer, default=0)
    violation_count: Mapped[int] = mapped_column(Integer, default=0)

    assigned_title: Mapped[str | None] = mapped_column(String(50), default=None)

    __table_args__ = (UniqueConstraint("user_id", "month", "year"),)

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
            assigned_title=UserTitle(self.assigned_title)
            if self.assigned_title
            else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: MonthlyUserStats) -> "MonthlyUserStatsModel":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            month=entity.month,
            year=entity.year,
            total_activity_hours=entity.total_activity_hours,
            total_bonus_points=entity.total_bonus_points,
            late_count=entity.late_count,
            absent_count=entity.absent_count,
            violation_count=entity.violation_count,
            assigned_title=entity.assigned_title.value
            if entity.assigned_title
            else None,
        )
