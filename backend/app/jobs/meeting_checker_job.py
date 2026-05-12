"""
Meeting Checker Job

Scheduled job that runs at 23:59 daily to check for meetings that have ended
and create violations for participants who didn't check in.
Uses Dishka for dependency injection and CheckMeetingAttendanceUseCase for business logic.
"""

from datetime import date
from typing import Optional

from dishka import AsyncContainer
from loguru import logger

from app.meeting.application.use_cases import CheckMeetingAttendanceUseCase
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def check_meeting_attendance(
    container: AsyncContainer, target_date: Optional[date] = None
) -> None:
    """
    Check for ended meetings (target_date) with require_check_in=True
    and create violations for participants who didn't attend.
    Resolves CheckMeetingAttendanceUseCase from Dishka container.
    """
    logger.info(f"🔍 [Meeting Checker] Starting meeting check for {target_date or 'today'}...")

    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(CheckMeetingAttendanceUseCase)
                count = await use_case.execute(target_date=target_date)
                logger.info(f"✅ [Meeting Checker] Completed - Violations created: {count}")
            finally:
                _request_container_context.reset(token)
    except Exception as e:
        logger.error(f"❌ [Meeting Checker] Job failed: {e}")
        logger.exception(e)
