"""
Notifications Housekeeping Background Job.
Scheduled by APScheduler to run daily at 03:00, resolving CleanExpiredNotificationsUseCase
from the Dishka request container context to prune read notifications older than 30 days.
"""

from dishka import AsyncContainer
from loguru import logger

from app.reminder.application.clean_expired_notifications_use_case import (
    CleanExpiredNotificationsUseCase,
)
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def clean_expired_notifications_job(container: AsyncContainer) -> None:
    """
    Scheduled job that cleans read notifications older than retention days (default: 30 days).
    """
    logger.info(
        "🧹 [Notifications Housekeeping] Starting scheduled cleanup of expired notifications..."
    )
    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(CleanExpiredNotificationsUseCase)
                deleted_count = await use_case.execute(retention_days=30)
                logger.info(
                    f"✅ [Notifications Housekeeping] Successfully pruned {deleted_count} expired read notifications"
                )
            finally:
                _request_container_context.reset(token)
    except Exception as e:
        logger.error(f"❌ [Notifications Housekeeping] Job failed: {e}")
        logger.exception(e)
