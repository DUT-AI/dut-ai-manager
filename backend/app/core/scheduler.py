"""
Scheduler module for background jobs using APScheduler.
Runs scheduled tasks like homework deadline checks.
"""

from app.jobs.homework_checker_job import check_overdue_homework_submissions
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    """Start the background scheduler with all registered jobs."""
    global scheduler

    scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")

    # Schedule homework check job at 23:00 (11 PM) every day
    scheduler.add_job(
        check_overdue_homework_submissions,
        CronTrigger(hour=23, minute=0, timezone="Asia/Ho_Chi_Minh"),
        id="homework_deadline_check",
        name="Check overdue homework submissions",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("📅 Scheduler started - Homework check scheduled for 23:00 daily")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("📅 Scheduler shutdown complete")
