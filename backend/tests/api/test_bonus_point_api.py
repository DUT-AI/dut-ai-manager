"""
API Tests for Bonus Point Controller (/api/v1/bonus-points).
Covers CRUD endpoints, filters, restore, and error responses (401, 403, 404, 422).
"""

from datetime import date
import pytest


@pytest.fixture
def test_bonus_point(admin_client, mock_current_user):
    """Tạo điểm cộng tạm thời và dọn dẹp sau khi kiểm thử."""
    payload = {
        "user_ids": [mock_current_user.id],
        "points": 5,
        "reason": "Hoàn thành xuất sắc nhiệm vụ",
        "date": date.today().isoformat(),
        "type": "OTHER",
    }
    res = admin_client.post("/api/v1/bonus-points", json=payload)
    assert res.status_code == 200
    items = res.json()["data"]
    item_id = items[0]["id"]

    yield items[0]

    admin_client.delete(f"/api/v1/bonus-points/{item_id}")


def test_list_bonus_points_unauthenticated(unauth_client):
    """Chưa đăng nhập khi lấy danh sách bonus points trả về 401."""
    res = unauth_client.get("/api/v1/bonus-points")
    assert res.status_code == 401


def test_list_bonus_points_as_member_returns_403(member_client):
    """Member không có BonusPointPermission.READ bị 403 Forbidden."""
    res = member_client.get("/api/v1/bonus-points")
    assert res.status_code == 403


def test_list_bonus_points_as_admin_success(admin_client, test_bonus_point):
    """Admin lấy danh sách điểm thưởng thành công."""
    res = admin_client.get("/api/v1/bonus-points?skip=0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_list_bonus_points_with_filters(admin_client, test_bonus_point, mock_current_user):
    """Lọc điểm thưởng theo user_id, month, year."""
    today = date.today()
    url = f"/api/v1/bonus-points?user_id={mock_current_user.id}&month={today.month}&year={today.year}"
    res = admin_client.get(url)
    assert res.status_code == 200
    assert res.json()["is_success"] is True


def test_create_bonus_point_as_member_returns_403(member_client, mock_current_user):
    """Member không có quyền tạo điểm thưởng (403)."""
    payload = {
        "user_ids": [mock_current_user.id],
        "points": 2,
        "reason": "Forbidden point",
        "date": date.today().isoformat(),
    }
    res = member_client.post("/api/v1/bonus-points", json=payload)
    assert res.status_code == 403


def test_create_bonus_point_missing_required_fields_returns_422(admin_client):
    """Tạo điểm thưởng thiếu trường bắt buộc trả về 422."""
    res = admin_client.post("/api/v1/bonus-points", json={"points": 5})
    assert res.status_code == 422


def test_create_bonus_point_success(admin_client, mock_current_user):
    """Admin tạo điểm thưởng thành công."""
    payload = {
        "user_ids": [mock_current_user.id],
        "points": 10,
        "reason": "Giải nhất Hackathon",
        "date": date.today().isoformat(),
        "type": "OTHER",
    }
    res = admin_client.post("/api/v1/bonus-points", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert len(data["data"]) > 0
    created_id = data["data"][0]["id"]

    admin_client.delete(f"/api/v1/bonus-points/{created_id}")


def test_update_bonus_point_as_member_returns_403(member_client, test_bonus_point):
    """Member không có quyền sửa điểm thưởng (403)."""
    payload = {"reason": "Member attempt"}
    res = member_client.put(f"/api/v1/bonus-points/{test_bonus_point['id']}", json=payload)
    assert res.status_code == 403


def test_update_bonus_point_success(admin_client, test_bonus_point):
    """Cập nhật điểm thưởng thành công."""
    payload = {"reason": "Cập nhật lý do thưởng", "points": 8}
    res = admin_client.put(f"/api/v1/bonus-points/{test_bonus_point['id']}", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["reason"] == "Cập nhật lý do thưởng"


def test_delete_and_restore_bonus_point(admin_client, mock_current_user):
    """Xóa và khôi phục điểm thưởng."""
    payload = {
        "user_ids": [mock_current_user.id],
        "points": 1,
        "reason": "Điểm tạm thời",
        "date": date.today().isoformat(),
    }
    res = admin_client.post("/api/v1/bonus-points", json=payload)
    item_id = res.json()["data"][0]["id"]

    # Delete
    del_res = admin_client.delete(f"/api/v1/bonus-points/{item_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_success"] is True

    # Restore
    res_restore = admin_client.put(f"/api/v1/bonus-points/{item_id}/restore")
    assert res_restore.status_code == 200
    assert res_restore.json()["is_success"] is True

    # Cleanup
    admin_client.delete(f"/api/v1/bonus-points/{item_id}")
