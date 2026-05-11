"""
Activity Scoring Job

Tự động tính điểm hoạt động dựa trên thời gian check-in/check-out.
Chạy mỗi 30 phút để tạo BonusPoint cho participants đã check-out.
"""

from datetime import datetime, timedelta
from typing import Optional
from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.meeting.infrastructure.repository import ParticipantRepository
from app.utils.datetime import get_current_utc7_time
from dishka import AsyncContainer
from loguru import logger


async def calculate_activity_points(
    container: AsyncContainer,
    since: Optional[datetime] = None
) -> int:
    """
    Tính điểm cho các participants đã check-out.
    Trả về số BonusPoint records đã tạo.
    """
    if since is None:
        since = get_current_utc7_time() - timedelta(hours=1)

    logger.info(f"🔍 [Activity Scoring] Starting point calculation since {since}...")

    try:
        async with container() as request_container:
            participant_repo = await request_container.get(ParticipantRepository)
            bonus_point_repo = await request_container.get(BonusPointRepository)

            # Lấy participants đã check-out sau `since`
            participants = participant_repo.get_completed_since(since)

            count = 0
            for p in participants:
                if p.check_in_at and p.check_out_at:
                    # Tính giờ hoạt động: +1 điểm/giờ
                    duration = (p.check_out_at - p.check_in_at).total_seconds()
                    hours = duration / 3600
                    points = int(round(hours))

                    if points > 0:
                        # Kiểm tra đã có BonusPoint cho participant này chưa
                        # (tránh tạo duplicate)
                        existing = bonus_point_repo.get_by_user_and_reason_and_date(
                            user_id=p.user_id,
                            reason=f"Hoạt động tại CLB",
                            date=p.check_out_at.date(),
                        )

                        if not existing:
                            bonus = BonusPoint(
                                user_id=p.user_id,
                                points=points,
                                reason=f"Hoạt động tại CLB: {hours:.2f} giờ",
                                date=get_current_utc7_time(),
                            )
                            bonus_point_repo.save(bonus)
                            count += 1
                            logger.info(
                                f"✅ Activity points: user={p.user_id}, "
                                f"hours={hours:.2f}, points={points}"
                            )

            logger.info(f"✅ [Activity Scoring] Completed - {count} records created")
            return count

    except Exception as e:
        logger.error(f"❌ [Activity Scoring] Job failed: {e}")
        logger.exception(e)
        return 0
