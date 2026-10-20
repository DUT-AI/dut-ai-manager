"""
Reminder Scanner Background Job.
Scheduled by APScheduler to run every 30 minutes, resolving ScanAndSendRemindersUseCase
from the Dishka request container context.
"""

from datetime import datetime
from dishka import AsyncContainer
from loguru import logger

from app.reminder.application.scan_and_send_reminders_use_case import (
    ScanAndSendRemindersUseCase,
)
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def scan_and_send_reminders(container: AsyncContainer) -> None:
    """
    Scheduled job that checks for approaching deadlines and triggers reminders.
    """
    logger.info("⏰ [Reminder Scanner] Starting scheduled task & deadline reminder check...")
    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(ScanAndSendRemindersUseCase)
                res = await use_case.execute(dry_run=False)
                logger.info(
                    f"✅ [Reminder Scanner] Completed - Scanned: {res.total_tasks_scanned}, "
                    f"Sent: {res.total_reminders_sent}, Skipped: {res.total_skipped_already_sent}, "
                    f"Failed: {res.total_failed}"
                )
            finally:
                _request_container_context.reset(token)
    except Exception as e:
        logger.error(f"❌ [Reminder Scanner] Job failed: {e}")
        logger.exception(e)
