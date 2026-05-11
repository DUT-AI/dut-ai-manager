"""
Monthly Title Assignment Job

Chạy vào 00:01 ngày đầu tiên của tháng mới.
Xét danh hiệu cho tháng vừa kết thúc và lưu vào DB.
"""

from datetime import datetime, timedelta
from typing import Optional
from app.user.domain.monthly_stats import MonthlyUserStats
from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
from app.user.infrastructure.repository import UserRepository
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.violation.infrastructure.repository import ViolationRepository
from app.utils.datetime import get_current_utc7_time
from dishka import AsyncContainer
from loguru import logger


async def assign_monthly_titles(
    container: AsyncContainer,
    target_month: Optional[int] = None,
    target_year: Optional[int] = None,
) -> int:
    """
    Xét danh hiệu cho tháng target và lưu vào DB.
    Trả về số users được xét.
    """
    now = get_current_utc7_time()

    if target_month is None or target_year is None:
        # Mặc định xét tháng trước
        first_day_of_month = now.replace(day=1)
        last_month = first_day_of_month - timedelta(days=1)
        target_month = last_month.month
        target_year = last_month.year

    logger.info(
        f"🏆 [Monthly Title] Starting assignment for {target_month}/{target_year}..."
    )

    try:
        async with container() as request_container:
            stats_repo = await request_container.get(MonthlyUserStatsRepository)
            bonus_repo = await request_container.get(BonusPointRepository)
            violation_repo = await request_container.get(ViolationRepository)
            user_repo = await request_container.get(UserRepository)

            # Lấy tất cả users active
            users = user_repo.get_active_users()

            count = 0
            for user in users:
                try:
                    # 1. Lấy thống kê tháng
                    bonus_points = bonus_repo.get_by_user_id(
                        user.id, target_month, target_year
                    )
                    total_bonus = sum(bp.points for bp in bonus_points)

                    violations = violation_repo.get_by_month(
                        user.id, target_month, target_year
                    )
                    violation_count = len(violations)

                    late_count = sum(
                        1 for v in violations if "trễ" in v.reason.lower()
                    )
                    absent_count = sum(
                        1
                        for v in violations
                        if "vắng" in v.reason.lower() or "không" in v.reason.lower()
                    )

                    # 2. Tính toán
                    stats = MonthlyUserStats(
                        user_id=user.id,
                        month=target_month,
                        year=target_year,
                        total_activity_hours=float(total_bonus),
                        total_bonus_points=total_bonus,
                        late_count=late_count,
                        absent_count=absent_count,
                        violation_count=violation_count,
                    )

                    # 3. Xét danh hiệu
                    title = stats.calculate_title()
                    stats.assigned_title = title

                    # 4. Lưu vào DB
                    stats_repo.save(stats)

                    logger.info(
                        f"🏆 Title assigned: user={user.id}, "
                        f"month={target_month}/{target_year}, title={title.value}"
                    )
                    count += 1

                except Exception as e:
                    logger.error(
                        f"❌ Failed to assign title for user {user.id}: {e}"
                    )

            logger.info(
                f"✅ [Monthly Title] Completed: {count} users processed"
            )
            return count

    except Exception as e:
        logger.error(f"❌ [Monthly Title] Job failed: {e}")
        logger.exception(e)
        return 0
