from datetime import date
from typing import Annotated, List

from app.core.deps import CurrentUser
from app.report.application.use_cases import (GetBonusPointReportUseCase,
                                              GetDailySummaryUseCase,
                                              GetDashboardOverviewUseCase,
                                              GetMonthlyActivityDatesUseCase,
                                              GetViolationReportUseCase)
from app.report.deps import (get_bonus_point_report_uc, get_daily_summary_uc,
                             get_dashboard_overview_uc,
                             get_monthly_activity_dates_uc,
                             get_violation_report_uc)
from app.report.schemas import (DailySummaryResponse,
                                DashboardOverviewResponse, ReportResponse)
from app.schemas.response import ApiResponse
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/daily-summary", response_model=ApiResponse[DailySummaryResponse])
async def get_daily_summary(
    uc: Annotated[GetDailySummaryUseCase, Depends(get_daily_summary_uc)],
    _current_user: CurrentUser,
    target_date: date = Query(alias="date"),
):
    """Lấy tổng hợp hoạt động (yêu cầu, điểm, vi phạm) trong một ngày cụ thể"""
    summary = uc.execute(target_date)
    return ApiResponse.success(data=summary)


@router.get("/monthly-stats", response_model=ApiResponse[List[date]])
async def get_monthly_activity_dates(
    uc: Annotated[
        GetMonthlyActivityDatesUseCase, Depends(get_monthly_activity_dates_uc)
    ],
    _current_user: CurrentUser,
    month: int,
    year: int,
):
    """Trả về danh sách các ngày có BẤT KỲ hoạt động nào trong tháng"""
    activity_dates = uc.execute(month, year)
    return ApiResponse.success(data=activity_dates)


@router.get(
    "/dashboard-overview", response_model=ApiResponse[DashboardOverviewResponse]
)
async def get_dashboard_overview(
    uc: Annotated[GetDashboardOverviewUseCase, Depends(get_dashboard_overview_uc)],
    current_user: CurrentUser,
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
):
    """
    Lấy thông tin tổng quan Dashboard cho người dùng trong một tháng cụ thể.
    Bao gồm: Yêu cầu xin phép, Điểm cộng, Vi phạm, Bài tập chưa nộp, Buổi sinh hoạt tham gia.
    """
    overview = uc.execute(user_id=current_user.id, month=month, year=year)
    return ApiResponse.success(data=overview)


@router.get("/bonus-points", response_model=ApiResponse[ReportResponse])
async def get_bonus_point_report(
    uc: Annotated[GetBonusPointReportUseCase, Depends(get_bonus_point_report_uc)],
    _current_user: CurrentUser,
    month: int = Query(None, description="Month"),
    year: int = Query(None, description="Year"),
    keyword: str = Query(None, description="Search keyword"),
):
    """Lấy báo cáo tổng hợp điểm cộng (xếp hạng)"""
    report = uc.execute(month=month, year=year, keyword=keyword)
    return ApiResponse.success(data=report)


@router.get("/violations", response_model=ApiResponse[ReportResponse])
async def get_violation_report(
    uc: Annotated[GetViolationReportUseCase, Depends(get_violation_report_uc)],
    _current_user: CurrentUser,
    month: int = Query(None, description="Month"),
    year: int = Query(None, description="Year"),
    keyword: str = Query(None, description="Search keyword"),
):
    """Lấy báo cáo tổng hợp vi phạm (xếp hạng)"""
    report = uc.execute(month=month, year=year, keyword=keyword)
    return ApiResponse.success(data=report)
