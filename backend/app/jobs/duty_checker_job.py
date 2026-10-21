"""
Duty Checker Job.

Scheduled job that runs at 23:59 daily to check for pending cleaning duties
and create violations for attendees who didn't submit proof by 22:00.
Uses Dishka for dependency injection and CheckOverdueDutiesUseCase for business logic.
"""

from datetime import date

from dishka import AsyncContainer
from loguru import logger

from app.duty.application.check_overdue_duties_use_case import (
    CheckOverdueDutiesUseCase,
)
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def check_overdue_duties(
    container: AsyncContainer, target_date: date | None = None
) -> None:
    """
    Check for pending cleaning duties on target_date (default today)
    and create violations for attendees if duty was not completed before 22:00.
    """
    logger.info(
        f"🧹 [Duty Checker] Starting duty check for {target_date or 'today'}..."
    )

    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(CheckOverdueDutiesUseCase)
                violations_count = await use_case.execute(target_date=target_date)
                logger.info(
                    f"✅ [Duty Checker] Completed - Violations created: {violations_count}"
                )
            finally:
                _request_container_context.reset(token)
    except Exception as e:
        logger.error(f"❌ [Duty Checker] Job failed: {e}")
        logger.exception(e)
