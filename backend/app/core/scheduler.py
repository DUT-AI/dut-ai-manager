"""
Scheduler module for background jobs using APScheduler.
Runs scheduled tasks like homework deadline checks.

NOTE: When running with multiple workers (e.g., gunicorn --workers 4),
the scheduler should only run in ONE worker to avoid duplicate job executions.
This is achieved using file-based locking - only the first worker to acquire
the lock will run the scheduler.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dishka import AsyncContainer
from loguru import logger

from app.jobs.activity_scoring_job import calculate_activity_points
from app.jobs.homework_checker_job import check_overdue_homework_submissions
from app.jobs.meeting_checker_job import check_meeting_attendance
from app.jobs.monthly_title_job import assign_monthly_titles

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


def start_scheduler(dishka_container: AsyncContainer) -> None:
    """Start the background scheduler with all registered jobs."""
    global scheduler

    logger.info("📅 Starting background scheduler...")

    scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")

    # Schedule homework check job at 23:59 every day
    scheduler.add_job(
        check_overdue_homework_submissions,
        CronTrigger(hour=23, minute=59, timezone="Asia/Ho_Chi_Minh"),
        id="homework_deadline_check",
        name="Check overdue homework submissions",
        replace_existing=True,
        kwargs={"container": dishka_container},
    )

    # Schedule meeting attendance check at 23:59 every day
    scheduler.add_job(
        check_meeting_attendance,
        CronTrigger(hour=23, minute=59, timezone="Asia/Ho_Chi_Minh"),
        id="meeting_attendance_check",
        name="Check meeting attendance",
        replace_existing=True,
        kwargs={"container": dishka_container},
    )

    # Schedule activity scoring check every 30 minutes
    scheduler.add_job(
        calculate_activity_points,
        CronTrigger(minute="0,30", timezone="Asia/Ho_Chi_Minh"),
        id="activity_scoring_job",
        name="Calculate activity points",
        replace_existing=True,
        kwargs={"container": dishka_container},
    )

    # Schedule monthly title assignment at 00:01 on the first day of the month
    scheduler.add_job(
        assign_monthly_titles,
        CronTrigger(day=1, hour=0, minute=1, timezone="Asia/Ho_Chi_Minh"),
        id="monthly_title_job",
        name="Assign monthly titles",
        replace_existing=True,
        kwargs={"container": dishka_container},
    )

    scheduler.start()
    logger.info("📅 Scheduler started - Homework & Meeting check at 23:59 daily")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("📅 Scheduler shutdown complete")
