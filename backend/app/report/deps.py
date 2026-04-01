from typing import Annotated

from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.homework.infrastructure.repository import HomeworkRepository
# Repositories
from app.meeting.infrastructure.repository import (MeetingRepository,
                                                   ParticipantRepository)
from app.permission_request.infrastructure.repository import \
  PermissionRequestRepository
# Use Cases
from app.report.application.use_cases import (GetBonusPointReportUseCase,
                                              GetDailySummaryUseCase,
                                              GetDashboardOverviewUseCase,
                                              GetMonthlyActivityDatesUseCase,
                                              GetViolationReportUseCase)
from app.shared.infrastructure.database import get_session
from app.user.infrastructure.repository import UserRepository
from app.violation.infrastructure.repository import ViolationRepository
from fastapi import Depends
from sqlmodel import Session


def get_daily_summary_uc(
    session: Annotated[Session, Depends(get_session)]
) -> GetDailySummaryUseCase:
    return GetDailySummaryUseCase(
        meeting_repo=MeetingRepository(session),
        permission_repo=PermissionRequestRepository(session),
        violation_repo=ViolationRepository(session),
        bonus_point_repo=BonusPointRepository(session),
    )


def get_monthly_activity_dates_uc(
    session: Annotated[Session, Depends(get_session)]
) -> GetMonthlyActivityDatesUseCase:
    return GetMonthlyActivityDatesUseCase(
        meeting_repo=MeetingRepository(session),
        permission_repo=PermissionRequestRepository(session),
        violation_repo=ViolationRepository(session),
        bonus_point_repo=BonusPointRepository(session),
    )


def get_dashboard_overview_uc(
    session: Annotated[Session, Depends(get_session)]
) -> GetDashboardOverviewUseCase:
    return GetDashboardOverviewUseCase(
        user_repo=UserRepository(session),
        meeting_repo=MeetingRepository(session),
        permission_repo=PermissionRequestRepository(session),
        violation_repo=ViolationRepository(session),
        bonus_point_repo=BonusPointRepository(session),
        homework_repo=HomeworkRepository(session),
    )


def get_bonus_point_report_uc(
    session: Annotated[Session, Depends(get_session)]
) -> GetBonusPointReportUseCase:
    return GetBonusPointReportUseCase(
        bonus_point_repo=BonusPointRepository(session),
        user_repo=UserRepository(session),
    )


def get_violation_report_uc(
    session: Annotated[Session, Depends(get_session)]
) -> GetViolationReportUseCase:
    return GetViolationReportUseCase(
        violation_repo=ViolationRepository(session),
        user_repo=UserRepository(session),
    )
