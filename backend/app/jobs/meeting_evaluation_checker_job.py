"""
Meeting Evaluation Checker Job

Scheduled job that runs periodically to check for meetings that ended > 24 hours ago
and create violations for Trainer or Trainee who failed to complete their evaluations.
"""

from dishka import AsyncContainer
from loguru import logger

from app.meeting.application import CheckEvaluationDeadlineJobUseCase
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def check_meeting_evaluations(container: AsyncContainer) -> None:
    """
    Check for ended meetings with enable_evaluation=True that passed 24h deadline
    and automatically create violations for unsubmitted evaluations.
    """
    logger.info("🔍 [Meeting Evaluation Checker] Starting evaluation deadline check...")

    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(
                    CheckEvaluationDeadlineJobUseCase
                )
                result = await use_case.execute()
                logger.info(
                    f"✅ [Meeting Evaluation Checker] Completed - "
                    f"Meetings scanned: {result['meetings_scanned']}, "
                    f"Trainee violations: {result['trainee_violations_created']}, "
                    f"Trainer violations: {result['trainer_violations_created']}"
                )
            finally:
                _request_container_context.reset(token)
    except Exception as e:
        logger.error(f"❌ [Meeting Evaluation Checker] Job failed: {e}")
        logger.exception(e)
