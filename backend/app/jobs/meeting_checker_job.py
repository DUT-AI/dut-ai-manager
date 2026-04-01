"""
Meeting Checker Job

Scheduled job that runs periodically to check for meetings that have ended
and create violations for participants who didn't check in.
Only processes meetings with require_check_in = True.
"""

from datetime import date

from app.api.v1.services.email_service import EmailService
from app.core.database import engine
from app.core.discord_service import DiscordService
from app.core.repository_factory import RepositoryFactory
from app.core.service_factory import ServiceFactory
from app.models.meeting import ParticipantStatus
from app.models.permission_request import RequestCategory
from app.schemas.activity import ViolationCreate
from app.shared.infrastructure.minio_service import MinioService
from app.utils.datetime import get_current_utc7_time
from loguru import logger
from sqlmodel import Session


async def check_meeting_attendance() -> None:
    """
    Check for ended meetings (today) with require_check_in=True
    and create violations for participants who didn't attend.

    Logic:
    1. Get current date (UTC+7)
    2. Find all meetings with:
       - require_check_in = True
       - start_time.date() == today
       - end_time <= now (already ended)
    3. For each meeting, check participants:
       - If status == 'chưa tham gia' (NOT_JOINED):
         - Check if user has Permission Request with category 'vắng sinh hoạt' for that date
         - If NO absence request → create Violation
         - If HAS absence request → skip
    """
    logger.info("🔍 [Meeting Checker] Starting meeting attendance check...")

    now = get_current_utc7_time()
    today = now.date()
    logger.info(f"📅 Checking meetings ended on {today}")

    with Session(engine) as session:
        repo_factory = RepositoryFactory(session)

        # Get ended meetings requiring check-in for today
        ended_meetings = repo_factory.meeting.get_ended_meetings_requiring_checkin(
            today
        )

        if not ended_meetings:
            logger.info(
                "✅ [Meeting Checker] No ended meetings requiring check-in found"
            )
            return

        logger.info(
            f"📋 Found {len(ended_meetings)} ended meetings to check attendance"
        )

        # We need ServiceFactory to create violations
        minio_service = MinioService()
        discord_service = DiscordService()
        email_service = EmailService()
        service_factory = ServiceFactory(
            repo_factory, minio_service, discord_service, email_service
        )

        violations_created = 0
        skipped_with_permission = 0
        already_checked_in = 0

        for meeting in ended_meetings:
            logger.info(
                f"📌 Checking meeting: '{meeting.title}' "
                f"({meeting.start_time} - {meeting.end_time})"
            )

            meeting_date = meeting.start_time.date()

            for participant in meeting.participants:
                if participant.is_deleted:
                    continue

                if participant.status == ParticipantStatus.JOINED:
                    already_checked_in += 1
                    continue

                user_id = participant.user_id

                # Check if user has absence permission for this date
                has_absence = (
                    repo_factory.permission_request.has_absence_request_for_date(
                        user_id=user_id, target_date=meeting_date
                    )
                )

                if has_absence:
                    logger.debug(
                        f"⏭️ User {user_id} has absence permission for "
                        f"meeting '{meeting.title}' - skipping"
                    )
                    skipped_with_permission += 1
                    continue

                # Create violation for absent user
                violation_data = ViolationCreate(
                    user_ids=[user_id],
                    reason=f"Vắng buổi sinh hoạt: {meeting.title}",
                    date=now,
                )

                try:
                    await service_factory.violation.create(
                        violation_data, is_system=True
                    )
                    violations_created += 1
                    logger.info(
                        f"⚠️ Created violation for user {user_id}: "
                        f"absent from '{meeting.title}'"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to create violation for user {user_id}: {e}"
                    )

        logger.info(
            f"✅ [Meeting Checker] Completed - "
            f"Violations created: {violations_created}, "
            f"Skipped (has permission): {skipped_with_permission}, "
            f"Already checked in: {already_checked_in}"
        )
