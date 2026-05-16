"""
Activity Scoring Job

Tự động tính điểm hoạt động dựa trên thời gian check-in/check-out.
Chạy mỗi 30 phút để tạo BonusPoint cho participants đã check-out.
"""

from datetime import datetime

from dishka import AsyncContainer
from loguru import logger

from app.bonus_point.application.use_cases import CalculateActivityPointsUseCase
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def calculate_activity_points(
    container: AsyncContainer, since: datetime | None = None
) -> int:
    """
    Tính điểm cho các participants đã check-out.
    Trả về số BonusPoint records đã tạo.
    """
    logger.info(f"🔍 [Activity Scoring] Starting point calculation since {since}...")

    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(CalculateActivityPointsUseCase)
                count = use_case.execute(since=since)
                logger.info(
                    f"✅ [Activity Scoring] Completed - {count} records created"
                )
                return count
            finally:
                _request_container_context.reset(token)

    except Exception as e:
        logger.error(f"❌ [Activity Scoring] Job failed: {e}")
        logger.exception(e)
        return 0
