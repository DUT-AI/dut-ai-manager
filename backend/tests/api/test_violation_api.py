"""
API Tests for Violation Controller (/api/v1/violations).
Covers CRUD endpoints, filters, bulk delete, restore, and error responses (401, 403, 404, 422).
"""

from datetime import date, timedelta
import pytest


@pytest.fixture
def test_violation(admin_client, mock_current_user):
    """Tạo một vi phạm tạm thời và dọn dẹp sau khi kiểm thử."""
    payload = {
        "user_ids": [mock_current_user.id],
        "reason": "Đi trễ họp sáng",
        "date": date.today().isoformat(),
    }
    res = admin_client.post("/api/v1/violations", json=payload)
    assert res.status_code == 200
    items = res.json()["data"]
    item_id = items[0]["id"]

    yield items[0]

    admin_client.delete(f"/api/v1/violations/{item_id}")


def test_list_violations_unauthenticated(unauth_client):
    """Chưa đăng nhập truy cập /violations trả về 401."""
    res = unauth_client.get("/api/v1/violations")
    assert res.status_code == 401


def test_list_violations_as_member_returns_403(member_client):
    """Member không có ViolationPermission.READ bị 403 Forbidden."""
    res = member_client.get("/api/v1/violations")
    assert res.status_code == 403


def test_list_violations_as_admin_success(admin_client, test_violation):
    """Admin lấy danh sách vi phạm thành công."""
    res = admin_client.get("/api/v1/violations?skip=0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_list_violations_with_filters(admin_client, test_violation, mock_current_user):
    """Lấy danh sách vi phạm có bộ lọc user_id, month, year."""
    today = date.today()
    url = f"/api/v1/violations?user_id={mock_current_user.id}&month={today.month}&year={today.year}"
    res = admin_client.get(url)
    assert res.status_code == 200
    assert res.json()["is_success"] is True


def test_create_violation_as_member_returns_403(member_client, mock_current_user):
    """Member không có quyền tạo vi phạm (403)."""
    payload = {
        "user_ids": [mock_current_user.id],
        "reason": "Forbidden",
        "date": date.today().isoformat(),
    }
    res = member_client.post("/api/v1/violations", json=payload)
    assert res.status_code == 403


def test_create_violation_missing_fields_returns_422(admin_client):
    """Tạo vi phạm thiếu reason trả về 422."""
    res = admin_client.post("/api/v1/violations", json={"user_ids": [1]})
    assert res.status_code == 422


def test_create_violation_success(admin_client, mock_current_user):
    """Admin tạo vi phạm thành công."""
    payload = {
        "user_ids": [mock_current_user.id],
        "reason": "Không nộp báo cáo tuần",
        "date": date.today().isoformat(),
    }
    res = admin_client.post("/api/v1/violations", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert len(data["data"]) > 0
    created_id = data["data"][0]["id"]

    admin_client.delete(f"/api/v1/violations/{created_id}")


def test_update_violation_as_member_returns_403(member_client, test_violation):
    """Member không có quyền sửa vi phạm (403)."""
    payload = {"reason": "Update attempt"}
    res = member_client.put(f"/api/v1/violations/{test_violation['id']}", json=payload)
    assert res.status_code == 403


def test_update_violation_success(admin_client, test_violation):
    """Cập nhật thông tin vi phạm thành công."""
    payload = {"reason": "Lý do đã được cập nhật"}
    res = admin_client.put(f"/api/v1/violations/{test_violation['id']}", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["reason"] == "Lý do đã được cập nhật"


def test_bulk_delete_violations(admin_client, mock_current_user):
    """Xóa hàng loạt vi phạm."""
    payload = {
        "user_ids": [mock_current_user.id],
        "reason": "Vi phạm tạm",
        "date": date.today().isoformat(),
    }
    res = admin_client.post("/api/v1/violations", json=payload)
    item_id = res.json()["data"][0]["id"]

    bulk_res = admin_client.post("/api/v1/violations/bulk-delete", json={"ids": [item_id]})
    assert bulk_res.status_code == 200
    assert bulk_res.json()["is_success"] is True


def test_delete_and_restore_violation(admin_client, mock_current_user):
    """Quy trình Xóa mềm và Khôi phục vi phạm."""
    payload = {
        "user_ids": [mock_current_user.id],
        "reason": "Vi phạm để xóa",
        "date": date.today().isoformat(),
    }
    res = admin_client.post("/api/v1/violations", json=payload)
    item_id = res.json()["data"][0]["id"]

    # Delete
    del_res = admin_client.delete(f"/api/v1/violations/{item_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_success"] is True

    # Restore
    res_restore = admin_client.put(f"/api/v1/violations/{item_id}/restore")
    assert res_restore.status_code == 200
    assert res_restore.json()["is_success"] is True

    # Cleanup
    admin_client.delete(f"/api/v1/violations/{item_id}")
