"""
Test script to manually run the homework checker job.

Usage:
    cd backend
    python -m tests.test_homework_checker
"""

import asyncio

import tests  # noqa: F401
from dishka import make_async_container

from app.auth.providers import AuthModuleProvider
from app.billing.providers import BillingModuleProvider
from app.bonus_point.providers import BonusPointModuleProvider
from app.expense.providers import ExpenseModuleProvider
from app.homework.providers import HomeworkModuleProvider
from app.jobs.homework_checker_job import check_overdue_homework_submissions
from app.meeting.providers import MeetingModuleProvider
from app.permission_request.providers import PermissionRequestModuleProvider
from app.rbac.providers import RbacModuleProvider
from app.report.providers import ReportModuleProvider
from app.shared.providers import InfrastructureProvider
from app.team.providers import TeamModuleProvider
from app.user.providers import UserModuleProvider
from app.violation.providers import ViolationModuleProvider
from app.zalo.providers import ZaloModuleProvider


async def main():
    print("=" * 60)
    print("Testing Homework Checker Job")
    print("=" * 60)

    container = make_async_container(
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

    try:
        await check_overdue_homework_submissions(container)
    finally:
        await container.close()

    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

