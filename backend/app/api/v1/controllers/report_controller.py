# --- Report Endpoints ---

from datetime import date

from app.core.deps import CurrentUser, ServiceFactoryDI
from app.schemas.activity import DailySummaryResponse
from app.schemas.response import ApiResponse
from fastapi import APIRouter, Query

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily-summary", response_model=ApiResponse[DailySummaryResponse])
async def get_daily_summary(
    _current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
    target_date: date = Query(alias="date"),
):
    """Retrieve all activities (requests, points, violations) for a specific date"""
    summary = service_factory.report.get_daily_summary(target_date)
    return ApiResponse.success(data=summary)


@router.get("/monthly-stats", response_model=ApiResponse[list[date]])
async def get_monthly_activity_dates(
    month: int,
    year: int,
    _current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
):
    """Returns a list of dates that have ANY activity in the given month"""
    activity_dates = service_factory.report.get_monthly_activity_dates(month, year)
    return ApiResponse.success(data=activity_dates)


@router.get("/dashboard-overview", response_model=ApiResponse)
async def get_dashboard_overview(
    current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
):
    """
    Get dashboard overview for the current user in a specific month.
    Includes:
    - Permission requests
    - Bonus points
    - Violations
    - Unsubmitted homework (all time pending)
    - Meetings (participating in month)
    """
    overview = service_factory.report.get_dashboard_overview(
        user_id=current_user.id, month=month, year=year
    )
    return ApiResponse.success(data=overview)


@router.get("/bonus-points", response_model=ApiResponse)
async def get_bonus_point_report(
    _current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
    month: int = Query(None, description="Month"),
    year: int = Query(None, description="Year"),
    keyword: str = Query(None, description="Search keyword"),
):
    """Get aggregated bonus point report"""
    report = service_factory.report.get_bonus_point_report(
        month=month, year=year, keyword=keyword
    )
    return ApiResponse.success(data=report)


@router.get("/violations", response_model=ApiResponse)
async def get_violation_report(
    _current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
    month: int = Query(None, description="Month"),
    year: int = Query(None, description="Year"),
    keyword: str = Query(None, description="Search keyword"),
):
    """Get aggregated violation report"""
    report = service_factory.report.get_violation_report(
        month=month, year=year, keyword=keyword
    )
    return ApiResponse.success(data=report)
