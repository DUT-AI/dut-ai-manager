"""
Scheduler module for background jobs using APScheduler.
Runs scheduled tasks like homework deadline checks.

NOTE: When running with multiple workers (e.g., gunicorn --workers 4),
the scheduler should only run in ONE worker to avoid duplicate job executions.
This is achieved using file-based locking - only the first worker to acquire
the lock will run the scheduler.
"""

import fcntl
import os

from app.jobs.homework_checker_job import check_overdue_homework_submissions
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None
# Lock file handle (keep it open to maintain the lock)
_lock_file = None


def _acquire_scheduler_lock() -> bool:
    """Try to acquire an exclusive lock for running the scheduler.

    Returns True if this process should run the scheduler, False otherwise.
    """
    global _lock_file

    lock_path = "/tmp/dut_ai_scheduler.lock"

    try:
        _lock_file = open(lock_path, "w")
        # Try to acquire exclusive lock (non-blocking)
        fcntl.flock(_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Write PID to lock file for debugging
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
        return True
    except (IOError, OSError):
        # Another process has the lock
        if _lock_file:
            _lock_file.close()
            _lock_file = None
        return False


def start_scheduler() -> None:
    """Start the background scheduler with all registered jobs.

    Uses file locking to ensure only ONE worker runs the scheduler,
    even across multiple Gunicorn/Uvicorn workers.
    """
    global scheduler

    # Check if scheduler should be enabled (default: True for backward compatibility)
    scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

    if not scheduler_enabled:
        logger.info("📅 Scheduler disabled for this worker (SCHEDULER_ENABLED=false)")
        return

    # Try to acquire the scheduler lock
    if not _acquire_scheduler_lock():
        logger.info(
            f"📅 Scheduler skipped for worker {os.getpid()} (another worker has the lock)"
        )
        return

    logger.info(f"📅 Worker {os.getpid()} acquired scheduler lock")

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
