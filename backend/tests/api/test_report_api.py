"""
API Tests for Report Controller (/api/v1/reports).
Covers success responses, 401 Unauthorized, and 422 Unprocessable Entity.
"""

from datetime import date
import pytest


def test_get_daily_summary_success(api_client):
    """Lấy báo cáo tổng hợp hoạt động hàng ngày."""
    today = date.today().isoformat()
    res = api_client.get(f"/api/v1/reports/daily-summary?date={today}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert "date" in data["data"]


def test_get_daily_summary_missing_date_returns_422(api_client):
    """Thiếu tham số bắt buộc 'date' phải trả về lỗi 422."""
    res = api_client.get("/api/v1/reports/daily-summary")
    assert res.status_code == 422


def test_get_daily_summary_unauthenticated_returns_401(unauth_client):
    """Chưa đăng nhập khi gọi daily summary phải nhận về 401."""
    today = date.today().isoformat()
    res = unauth_client.get(f"/api/v1/reports/daily-summary?date={today}")
    assert res.status_code == 401


def test_get_monthly_stats_success(api_client):
    """Lấy danh sách các ngày có hoạt động trong tháng."""
    res = api_client.get("/api/v1/reports/monthly-stats?month=10&year=2026")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_dashboard_overview_success(api_client):
    """Lấy dữ liệu tổng quan Dashboard cho người dùng."""
    res = api_client.get("/api/v1/reports/dashboard-overview?month=10&year=2026")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_get_bonus_points_report_success(api_client):
    """Lấy báo cáo xếp hạng điểm cộng."""
    res = api_client.get("/api/v1/reports/bonus-points?month=10&year=2026")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_get_violations_report_success(api_client):
    """Lấy báo cáo xếp hạng vi phạm."""
    res = api_client.get("/api/v1/reports/violations?month=10&year=2026")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_get_titles_report_success(api_client):
    """Lấy báo cáo danh hiệu các tháng."""
    res = api_client.get("/api/v1/reports/titles?month=10&year=2026")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_current_title_success(api_client, mock_current_user):
    """Lấy danh hiệu hiện tại của user."""
    res = api_client.get(f"/api/v1/reports/users/{mock_current_user.id}/current-title")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_get_participation_analysis_success(api_client, mock_current_user):
    """Lấy phân tích tỉ lệ tham gia sinh hoạt."""
    res = api_client.get(
        f"/api/v1/reports/users/{mock_current_user.id}/participation?month=10&year=2026"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_get_participation_leaderboard_success(api_client):
    """Lấy bảng xếp hạng tham gia sinh hoạt."""
    res = api_client.get("/api/v1/reports/participation/leaderboard?month=10&year=2026")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_get_activity_trend_success(api_client):
    """Lấy dữ liệu xu hướng hoạt động theo tuần/tháng."""
    res = api_client.get("/api/v1/reports/activity-trend?month=10&year=2026")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
