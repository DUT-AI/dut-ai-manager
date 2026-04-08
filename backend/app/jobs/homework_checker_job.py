"""
Homework Checker Job

Scheduled job that runs at 23:59 daily to check for overdue homework submissions.
Uses Dishka for dependency injection and CheckOverdueHomeworkUseCase for business logic.
"""

from datetime import date
from typing import Optional
from app.homework.application.use_cases import CheckOverdueHomeworkUseCase
from dishka import AsyncContainer
from loguru import logger
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)


async def check_overdue_homework_submissions(
    container: AsyncContainer, target_date: Optional[date] = None
) -> None:
    """
    Check for homework submissions that are overdue (deadline = target_date) and create violations.
    Resolves CheckOverdueHomeworkUseCase from Dishka container.
    """
    logger.info(f"🔍 [Homework Checker] Starting homework check for {target_date or 'today'}...")

    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(CheckOverdueHomeworkUseCase)
                count = await use_case.execute(target_date=target_date)
                logger.info(f"✅ [Homework Checker] Completed - Violations created: {count}")
            finally:
                _request_container_context.reset(token)
    except Exception as e:
        logger.error(f"❌ [Homework Checker] Job failed: {e}")
        logger.exception(e)
