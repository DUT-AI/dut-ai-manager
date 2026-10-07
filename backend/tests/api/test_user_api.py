"""
API Tests for User Controller (/api/v1/users).
Covers success responses, 401 Unauthorized, 403 Forbidden, and 404 Not Found.
"""

import pytest


def test_list_users_as_admin_success(admin_client):
    """Admin có thể xem danh sách toàn bộ users."""
    res = admin_client.get("/api/v1/users")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_list_users_with_search_keyword(admin_client):
    """Tìm kiếm users theo keyword."""
    res = admin_client.get("/api/v1/users?keyword=Admin")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_list_users_as_unauthenticated_returns_401(unauth_client):
    """Chưa đăng nhập khi gọi API /users phải trả về 401 Unauthorized."""
    res = unauth_client.get("/api/v1/users")
    assert res.status_code == 401


def test_list_users_as_member_returns_403(member_client):
    """User không có quyền UserPermission.READ phải nhận về 403 Forbidden."""
    res = member_client.get("/api/v1/users")
    assert res.status_code == 403


def test_download_user_import_template_success(admin_client):
    """Tải template Excel import user trả về file binary hợp lệ."""
    res = admin_client.get("/api/v1/users/template")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res.headers["content-type"]


def test_get_user_by_id_success(admin_client, mock_current_user):
    """Lấy thông tin chi tiết user theo ID."""
    res = admin_client.get(f"/api/v1/users/{mock_current_user.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["id"] == mock_current_user.id


def test_get_user_by_id_not_found(admin_client):
    """Tìm user với ID không tồn tại phải trả về 404 Not Found."""
    res = admin_client.get("/api/v1/users/99999999")
    assert res.status_code == 404


import uuid


def test_update_me_settings_success(member_client):
    """User tự cập nhật thông tin cá nhân (me/settings) với mã thẻ duy nhất."""
    unique_card = f"CARD_{uuid.uuid4().hex[:8]}"
    payload = {
        "discord_id": "test_discord_123",
        "check_in_card_code": unique_card,
    }
    res = member_client.put("/api/v1/users/me/settings", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["discord_id"] == "test_discord_123"
    assert data["data"]["check_in_card_code_configured"] is True


def test_update_me_settings_duplicate_card_returns_400(member_client):
    """Trùng mã thẻ check-in với người khác phải trả về 400 Bad Request."""
    payload = {
        "check_in_card_code": "CARD_999",  # Đã tồn tại trong DB
    }
    res = member_client.put("/api/v1/users/me/settings", json=payload)
    assert res.status_code == 400
    assert "Mã thẻ check-in đã được người khác sử dụng" in res.json()["message"]


def test_update_user_forbidden_for_member(member_client):
    """Member không có quyền sửa thông tin user khác (403 Forbidden)."""
    payload = {"name": "Hacked Name"}
    res = member_client.put("/api/v1/users/1", json=payload)
    assert res.status_code == 403


def test_delete_user_forbidden_for_member(member_client):
    """Member không có quyền xoá user (403 Forbidden)."""
    res = member_client.delete("/api/v1/users/1")
    assert res.status_code == 403
