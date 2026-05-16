from enum import Enum

from app.shared.domain.base_entity import BaseEntity


class UserTitle(str, Enum):
    """Các loại danh hiệu tháng"""

    ACTIVE = "ACTIVE"
    NORMAL = "NORMAL"
    POOR = "POOR"


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
        if self.violation_count >= 3:
            return UserTitle.POOR
        if self.total_bonus_points > 30:
            return UserTitle.ACTIVE
        return UserTitle.NORMAL
