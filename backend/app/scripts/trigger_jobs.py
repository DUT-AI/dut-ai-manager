import argparse
import asyncio
import os
import sys
from datetime import date, datetime
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Set environment variable to local if not set
if "ENVIRONMENT" not in os.environ:
    os.environ["ENVIRONMENT"] = "local"

from dishka import make_async_container
from loguru import logger

from app.auth.providers import AuthModuleProvider
from app.billing.providers import BillingModuleProvider
from app.bonus_point.providers import BonusPointModuleProvider
from app.core.events import bootstrap_events
from app.homework.providers import HomeworkModuleProvider
from app.jobs.activity_scoring_job import calculate_activity_points
from app.jobs.homework_checker_job import check_overdue_homework_submissions
from app.jobs.meeting_checker_job import check_meeting_attendance
from app.jobs.monthly_title_job import assign_monthly_titles
from app.meeting.providers import MeetingModuleProvider
from app.permission_request.providers import PermissionRequestModuleProvider
from app.report.providers import ReportModuleProvider
from app.shared.infrastructure.request_context import set_request_container
from app.shared.providers import InfrastructureProvider
from app.team.providers import TeamModuleProvider
from app.user.providers import UserModuleProvider
from app.violation.providers import ViolationModuleProvider
from app.zalo.providers import ZaloModuleProvider


async def run_jobs(target_date: date | None = None):
    logger.info(
        f"🎬 Initializing standalone job trigger script for date: {target_date or 'today'}..."
    )

    # Initialize container (same providers as in app/main.py)
    container = make_async_container(
        InfrastructureProvider(),
        AuthModuleProvider(),
        UserModuleProvider(),
        ViolationModuleProvider(),
        PermissionRequestModuleProvider(),
        ReportModuleProvider(),
        MeetingModuleProvider(),
        BonusPointModuleProvider(),
        HomeworkModuleProvider(),
        TeamModuleProvider(),
        BillingModuleProvider(),
        ZaloModuleProvider(),
    )

    # Set the container in contextvar for EventBus to use
    set_request_container(container)

    try:
        # 1. Kết nối Events (Quan trọng để AutomatedViolationHandler có thể nhận tin)
        logger.info("📡 Bootstrapping events...")
        await bootstrap_events(container)

        # 2. Chạy job kiểm tra bài tập
        logger.info("⌛ Triggering Homework Checker Job...")
        await check_overdue_homework_submissions(container, target_date=target_date)

        # # 3. Chạy job kiểm tra điểm danh
        logger.info("⌛ Triggering Meeting Checker Job...")
        await check_meeting_attendance(container, target_date=target_date)

        # # 4. Chạy job tính điểm hoạt động
        logger.info("⌛ Triggering Activity Scoring Job...")
        await calculate_activity_points(container)

        # # 5. Chạy job gán danh hiệu
        logger.info("⌛ Triggering Monthly Title Job...")
        await assign_monthly_titles(container)

        logger.success("🏁 All jobs executed successfully.")

    except Exception as e:
        logger.exception(f"❌ Error during job execution: {e}")
    finally:
        await container.close()
        logger.info("🛑 Container closed. Script exit.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger background jobs manually.")
    parser.add_argument(
        "--date",
        type=str,
        help="Target date in YYYY-MM-DD format (default: today)",
        default=None,
    )

    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error("❌ Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)

    try:
        asyncio.run(run_jobs(target_date))
    except KeyboardInterrupt:
        logger.info("👋 Script interrupted by user.")
