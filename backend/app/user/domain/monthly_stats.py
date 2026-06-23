from enum import Enum

from app.shared.domain.base_entity import BaseEntity


class UserTitle(str, Enum):
    """Các loại danh hiệu tháng"""

    ACTIVE = "Tích cực"
    NORMAL = "Bình thường"
    POOR = "Hoạt động kém"
    INACTIVE = "Chưa hoạt động"


class MonthlyUserStats(BaseEntity):
    """Thống kê và danh hiệu tháng của user"""

    user_id: int
    month: int
    year: int

    total_activity_hours: float = 0
    total_bonus_points: int = 0
    late_count: int = 0
    absent_count: int = 0
    violation_count: int = 0

    assigned_title: UserTitle | None = None

    def calculate_title(self) -> UserTitle:
        """Tính toán danh hiệu dựa trên thống kê"""
        if self.total_activity_hours == 0 and self.late_count == 0 and self.absent_count == 0 and self.total_bonus_points == 0 and self.violation_count == 0:
            return UserTitle.INACTIVE

        total_score = self.total_bonus_points - (2 * self.late_count + 5 * self.absent_count)

        if self.violation_count >= 3:
            return UserTitle.POOR
        elif total_score > 30:
            return UserTitle.ACTIVE
        else:
            return UserTitle.NORMAL
