"""
Monthly Title Assignment Job

Chạy vào 00:01 ngày đầu tiên của tháng mới.
Xét danh hiệu cho tháng vừa kết thúc và lưu vào DB.
"""

from typing import Optional

from dishka import AsyncContainer
from loguru import logger

from app.report.application.title_use_cases import AssignMonthlyTitlesUseCase
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def assign_monthly_titles(
    container: AsyncContainer,
    target_month: Optional[int] = None,
    target_year: Optional[int] = None,
) -> int:
    """
    Xét danh hiệu cho tháng target và lưu vào DB.
    Trả về số users được xét.
    """
    logger.info(
        f"🏆 [Monthly Title] Starting assignment for {target_month}/{target_year}..."
    )

    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(AssignMonthlyTitlesUseCase)
                count = use_case.execute(
                    target_month=target_month, target_year=target_year
                )
                logger.info(f"✅ [Monthly Title] Completed: {count} users processed")
                return count
            finally:
                _request_container_context.reset(token)

    except Exception as e:
        logger.error(f"❌ [Monthly Title] Job failed: {e}")
        logger.exception(e)
        return 0
