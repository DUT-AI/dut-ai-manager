"""
Homework Checker Job

Scheduled job that runs at 23:00 daily to check for overdue homework submissions.
Creates violations for users who haven't submitted their homework and don't have
a postponement permission request.
"""

from app.api.v1.services.email_service import EmailService
from app.core.database import engine
from app.core.discord_service import DiscordService
from app.core.repository_factory import RepositoryFactory
from app.core.service_factory import ServiceFactory
from app.schemas.activity import ViolationCreate
from app.shared.infrastructure.minio_service import MinioService
from app.utils.datetime import get_current_utc7_time
from loguru import logger
from sqlmodel import Session


async def check_overdue_homework_submissions() -> None:
    """
    Check for homework submissions that are overdue (deadline = today) and create violations.

    Logic:
    1. Get current date (UTC+7)
    2. Find all HomeworkSubmissions with:
       - status = 'chưa nộp' (NOT_SUBMITTED)
       - homework.deadline.date() == today
    3. For each submission:
       - Check if user has Permission Request with category 'tạm hoãn bài tập' for deadline date
       - If NO postponement request → create Violation
       - If HAS postponement request → skip
    """
    logger.info("🔍 [Homework Checker] Starting daily homework check...")

    today = get_current_utc7_time().date()
    logger.info(f"📅 Checking homeworks with deadline = {today}")

    # Create a new session for this job (not using request context)
    with Session(engine) as session:
        repo_factory = RepositoryFactory(session)
        minio_service = MinioService()
        discord_service = DiscordService()
        email_service = EmailService()
        service_factory = ServiceFactory(
            repo_factory, minio_service, discord_service, email_service
        )

        # Get all submissions that are not submitted and have deadline today
        overdue_submissions = (
            repo_factory.homework_submission.get_not_submitted_for_deadline_date(today)
        )

        if not overdue_submissions:
            logger.info("✅ [Homework Checker] No overdue submissions found for today")
            return

        logger.info(f"📋 Found {len(overdue_submissions)} overdue submissions to check")

        violations_created = 0
        skipped_with_permission = 0

        for submission in overdue_submissions:
            user_id = submission.owner_id
            homework = submission.homework
            deadline_date = homework.deadline.date() if homework else today

            # Check if user has postponement permission for the deadline date
            has_postpone = (
                repo_factory.permission_request.has_postpone_request_for_date(
                    user_id=user_id, target_date=deadline_date
                )
            )

            if has_postpone:
                logger.debug(
                    f"⏭️ User {user_id} has postponement for homework '{homework.title}' - skipping"
                )
                skipped_with_permission += 1
                continue

            # Create violation
            violation_data = ViolationCreate(
                user_ids=[user_id],
                reason=f"Không nộp bài tập: {homework.title}",
                date=get_current_utc7_time(),
            )

            try:
                await service_factory.violation.create(violation_data, is_system=True)
                violations_created += 1
                logger.info(
                    f"⚠️ Created violation for user {user_id}: '{homework.title}'"
                )
            except Exception as e:
                logger.error(f"❌ Failed to create violation for user {user_id}: {e}")

        logger.info(
            f"✅ [Homework Checker] Completed - "
            f"Violations created: {violations_created}, "
            f"Skipped (has permission): {skipped_with_permission}"
        )
