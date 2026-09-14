"""
Sync Legacy Homeworks & Rescan All Homework Violations Script.

Usage:
    python -m app.jobs.sync_legacy_homeworks [--dry-run]
"""

import sys
import asyncio
import argparse
from loguru import logger

from dishka import make_async_container

from app.auth.providers import AuthModuleProvider
from app.billing.providers import BillingModuleProvider
from app.bonus_point.providers import BonusPointModuleProvider
from app.expense.providers import ExpenseModuleProvider
from app.homework.application.checker_use_cases import RescanAllHomeworksUseCase
from app.homework.providers import HomeworkModuleProvider
from app.meeting.providers import MeetingModuleProvider
from app.permission_request.providers import PermissionRequestModuleProvider
from app.rbac.providers import RbacModuleProvider
from app.report.providers import ReportModuleProvider
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)
from app.shared.providers import InfrastructureProvider
from app.team.providers import TeamModuleProvider
from app.user.providers import UserModuleProvider
from app.violation.providers import ViolationModuleProvider
from app.zalo.providers import ZaloModuleProvider


def create_app_container():
    return make_async_container(
        InfrastructureProvider(),
        AuthModuleProvider(),
        UserModuleProvider(),
        RbacModuleProvider(),
        ViolationModuleProvider(),
        PermissionRequestModuleProvider(),
        ReportModuleProvider(),
        MeetingModuleProvider(),
        BonusPointModuleProvider(),
        HomeworkModuleProvider(),
        TeamModuleProvider(),
        BillingModuleProvider(),
        ZaloModuleProvider(),
        ExpenseModuleProvider(),
    )


async def run_sync_and_rescan(dry_run: bool = False) -> None:
    logger.info(f"🔍 [Rescan & Sync Job] Starting homework rescan (dry_run={dry_run})...")
    container = create_app_container()
    try:
        async with container() as request_container:
            token = set_request_container(request_container)
            try:
                use_case = await request_container.get(RescanAllHomeworksUseCase)
                if dry_run:
                    logger.info("ℹ️ Running in DRY-RUN mode. No changes will be committed.")
                    count = await use_case.execute(auto_sync_legacy=False)
                else:
                    count = await use_case.execute(auto_sync_legacy=True)
                logger.info(f"✅ [Rescan & Sync Job] Completed - Violations processed: {count}")
            finally:
                _request_container_context.reset(token)
    except Exception as e:
        logger.error(f"❌ [Rescan & Sync Job] Failed: {e}")
        logger.exception(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync legacy homeworks and rescan overdue violations.")
    parser.add_argument("--dry-run", action="store_true", help="Run without persisting changes.")
    args = parser.parse_args()

    asyncio.run(run_sync_and_rescan(dry_run=args.dry_run))
