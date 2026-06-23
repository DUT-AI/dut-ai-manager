from datetime import date
from typing import Optional

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query

from app.core.deps import CurrentUser
from app.report.application.title_use_cases import (
    GetCurrentTitleUseCase,
    GetMonthlyTitlesReportUseCase,
    TitleReportItem,
)
from app.report.application.participation_use_cases import (
    GetParticipationAnalysisUseCase,
    GetParticipationLeaderboardUseCase,
    ParticipationStats,
)
from app.report.application.trend_use_cases import (
    GetActivityTrendUseCase,
    ActivityTrendItem,
)
from app.report.application.use_cases import (
    GetBonusPointReportUseCase,
    GetDailySummaryUseCase,
    GetDashboardOverviewUseCase,
    GetMonthlyActivityDatesUseCase,
    GetViolationReportUseCase,
)
from app.report.schemas import (
    DailySummaryResponse,
    DashboardOverviewResponse,
    ReportResponse,
)
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/daily-summary", response_model=ApiResponse[DailySummaryResponse])
@inject
async def get_daily_summary(
    uc: FromDishka[GetDailySummaryUseCase],
    _current_user: CurrentUser,
    target_date: date = Query(alias="date"),
):
    """Lấy tổng hợp hoạt động (yêu cầu, điểm, vi phạm) trong một ngày cụ thể"""
    summary = uc.execute(target_date)
    return ApiResponse.success(data=summary)


@router.get("/monthly-stats", response_model=ApiResponse[list[date]])
@inject
async def get_monthly_activity_dates(
    uc: FromDishka[GetMonthlyActivityDatesUseCase],
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
@inject
async def get_dashboard_overview(
    uc: FromDishka[GetDashboardOverviewUseCase],
    current_user: CurrentUser,
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
):
    """
    Lấy thông tin tổng quan Dashboard cho người dùng trong một tháng cụ thể.
    Bao gồm: Yêu cầu xin phép, Điểm cộng, Vi phạm, Bài tập chưa nộp, Buổi sinh hoạt tham gia.
    """
    assert current_user.id is not None
    overview = uc.execute(user_id=current_user.id, month=month, year=year)
    return ApiResponse.success(data=overview)


@router.get("/bonus-points", response_model=ApiResponse[ReportResponse])
@inject
async def get_bonus_point_report(
    uc: FromDishka[GetBonusPointReportUseCase],
    _current_user: CurrentUser,
    month: int = Query(None, description="Month"),
    year: int = Query(None, description="Year"),
    keyword: str = Query(None, description="Search keyword"),
):
    """Lấy báo cáo tổng hợp điểm cộng (xếp hạng)"""
    report = uc.execute(month=month, year=year, keyword=keyword)
    return ApiResponse.success(data=report)


@router.get("/violations", response_model=ApiResponse[ReportResponse])
@inject
async def get_violation_report(
    uc: FromDishka[GetViolationReportUseCase],
    _current_user: CurrentUser,
    month: int = Query(None, description="Month"),
    year: int = Query(None, description="Year"),
    keyword: str = Query(None, description="Search keyword"),
):
    """Lấy báo cáo tổng hợp vi phạm (xếp hạng)"""
    report = uc.execute(month=month, year=year, keyword=keyword)
    return ApiResponse.success(data=report)


@router.get("/titles", response_model=ApiResponse[list[TitleReportItem]])
@inject
async def get_monthly_titles_report(
    uc: FromDishka[GetMonthlyTitlesReportUseCase],
    _current_user: CurrentUser,
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
):
    """Lấy bảng danh hiệu tháng"""
    report = uc.execute(month=month, year=year)
    return ApiResponse.success(data=report)


@router.get("/users/{user_id}/current-title", response_model=ApiResponse[Optional[str]])
@inject
async def get_user_current_title(
    user_id: int,
    uc: FromDishka[GetCurrentTitleUseCase],
    _current_user: CurrentUser,
):
    """Lấy danh hiệu hiện tại của user"""
    title = uc.execute(user_id=user_id)
    return ApiResponse.success(data=title)


@router.get("/users/{user_id}/participation", response_model=ApiResponse[ParticipationStats])
@inject
async def get_participation_analysis(
    user_id: int,
    uc: FromDishka[GetParticipationAnalysisUseCase],
    _current_user: CurrentUser,
    month: int = Query(...),
    year: int = Query(...),
):
    """Phân tích mức độ tham gia: số lần, giờ, tần suất, streak, tỉ lệ đúng giờ"""
    return ApiResponse.success(data=uc.execute(user_id, month, year))


@router.get("/participation/leaderboard", response_model=ApiResponse[list[ParticipationStats]])
@inject
async def get_participation_leaderboard(
    uc: FromDishka[GetParticipationLeaderboardUseCase],
    _current_user: CurrentUser,
    month: int = Query(...),
    year: int = Query(...),
):
    """Bảng xếp hạng mức độ tham gia trong tháng."""
    return ApiResponse.success(data=uc.execute(month, year))


@router.get("/activity-trend", response_model=ApiResponse[list[ActivityTrendItem]])
@inject
async def get_activity_trend(
    uc: FromDishka[GetActivityTrendUseCase],
    _current_user: CurrentUser,
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
    mode: str = Query("week", description="Aggregation mode: 'week' or 'month'"),
):
    """Lấy dữ liệu xu hướng hoạt động (điểm cộng + vi phạm) theo tuần hoặc tháng."""
    return ApiResponse.success(data=uc.execute(month, year, mode))
