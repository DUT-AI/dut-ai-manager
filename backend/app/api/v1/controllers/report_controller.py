# --- Report Endpoints ---

from datetime import date

from app.core.deps import CurrentUser, ServiceFactoryDI
from app.schemas.activity import DailySummaryResponse
from app.schemas.response import ApiResponse
from fastapi import APIRouter, Query

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily-summary", response_model=ApiResponse[DailySummaryResponse])
async def get_daily_summary(
    current_user: CurrentUser,
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
    current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
):
    """Returns a list of dates that have ANY activity in the given month"""
    activity_dates = service_factory.report.get_monthly_activity_dates(month, year)
    return ApiResponse.success(data=activity_dates)
