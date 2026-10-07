"""
API Tests for Team Controller (/api/v1/teams).
Covers success responses, 401 Unauthorized, 403 Forbidden, 404 Not Found, and 422 Bad Request.
"""

import pytest


def test_list_teams_as_admin_success(admin_client):
    """Admin có quyền TeamPermission.READ lấy được danh sách các teams."""
    res = admin_client.get("/api/v1/teams")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_list_teams_unauthenticated_returns_401(unauth_client):
    """Chưa đăng nhập khi gọi /api/v1/teams phải trả về 401."""
    res = unauth_client.get("/api/v1/teams")
    assert res.status_code == 401


def test_list_teams_as_member_returns_403(member_client):
    """Member không có quyền TeamPermission.READ bị chặn 403 Forbidden."""
    res = member_client.get("/api/v1/teams")
    assert res.status_code == 403


def test_get_team_by_id_not_found(admin_client):
    """Truy vấn team ID không tồn tại phải trả về 404 Not Found."""
    res = admin_client.get("/api/v1/teams/99999999")
    assert res.status_code == 404


def test_get_team_as_member_returns_403(member_client):
    """Member không có quyền xem chi tiết team bị chặn 403 Forbidden."""
    res = member_client.get("/api/v1/teams/1")
    assert res.status_code == 403


def test_create_team_as_member_returns_403(member_client):
    """Member không có quyền tạo team (403 Forbidden)."""
    payload = {"name": "AI Team Test", "description": "Test team"}
    res = member_client.post("/api/v1/teams", json=payload)
    assert res.status_code == 403


def test_create_team_missing_name_returns_422(admin_client):
    """Tạo team thiếu tên bắt buộc phải nhận về 422 Unprocessable Entity."""
    payload = {"description": "Missing name field"}
    res = admin_client.post("/api/v1/teams", json=payload)
    assert res.status_code == 422


def test_update_team_as_member_returns_403(member_client):
    """Member không có quyền cập nhật team (403 Forbidden)."""
    payload = {"name": "Updated Team"}
    res = member_client.put("/api/v1/teams/1", json=payload)
    assert res.status_code == 403


def test_update_team_not_found(admin_client):
    """Cập nhật team không tồn tại trả về 404 Not Found."""
    payload = {"name": "Nonexistent Team"}
    res = admin_client.put("/api/v1/teams/99999999", json=payload)
    assert res.status_code == 404


def test_delete_team_as_member_returns_403(member_client):
    """Member không có quyền xoá team (403 Forbidden)."""
    res = member_client.delete("/api/v1/teams/1")
    assert res.status_code == 403
