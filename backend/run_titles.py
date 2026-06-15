import asyncio
from dishka import make_async_container
from app.shared.providers import InfrastructureProvider
from app.auth.providers import AuthModuleProvider
from app.user.providers import UserModuleProvider
from app.violation.providers import ViolationModuleProvider
from app.permission_request.providers import PermissionRequestModuleProvider
from app.report.providers import ReportModuleProvider
from app.meeting.providers import MeetingModuleProvider
from app.bonus_point.providers import BonusPointModuleProvider
from app.homework.providers import HomeworkModuleProvider
from app.team.providers import TeamModuleProvider
from app.billing.providers import BillingModuleProvider
from app.zalo.providers import ZaloModuleProvider
from app.report.application.title_use_cases import AssignMonthlyTitlesUseCase

async def run_titles():
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
    async with container() as request_container:
        uc = await request_container.get(AssignMonthlyTitlesUseCase)
        count = uc.execute(target_month=5, target_year=2026)
        print(f"SUCCESS: Assigned titles for {count} users in May 2026!")
    await container.close()

asyncio.run(run_titles())
