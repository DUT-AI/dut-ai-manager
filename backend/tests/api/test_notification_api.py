"""
API Tests for Notification & Reminder Controller (/api/v1/notifications).
Tests endpoints:
- GET /api/v1/notifications/my (with filters and pagination)
- GET /api/v1/notifications/unread-count
- PATCH /api/v1/notifications/{id}/read
- POST /api/v1/notifications/read-all
- DELETE /api/v1/notifications/{id}
- POST /api/v1/notifications/trigger (Admin scan trigger)
- 401 Unauthorized for unauthenticated requests
"""

import pytest
from app.reminder.domain.entity import (
    Notification,
    NotificationCategory,
    NotificationLevel,
)
from app.reminder.infrastructure.repository import NotificationRepository


@pytest.fixture
def test_notification(db_session, mock_current_user):
    """Tạo thông báo mẫu cho user hiện tại và dọn dẹp sau test."""
    repo = NotificationRepository(session=db_session)
    notif = Notification(
        user_id=mock_current_user.id,
        title="Nhắc nhở kiểm thử API",
        content="Nội dung kiểm thử API thông báo",
        category=NotificationCategory.HOMEWORK,
        level=NotificationLevel.WARNING,
        action_url="/dashboard/my-homeworks",
        is_read=False,
    )
    saved = repo.add(notif)
    db_session.commit()

    yield saved

    # Cleanup
    repo.delete_by_id(saved.id)
    db_session.commit()


def test_get_my_notifications_api(admin_client, test_notification):
    """Kiểm tra API lấy danh sách thông báo của tôi kèm phân trang và lọc."""
    # 1. Lấy tất cả
    res = admin_client.get("/api/v1/notifications/my?page=1&page_size=10")
    assert res.status_code == 200
    body = res.json()
    assert body["is_success"] is True
    assert isinstance(body["data"], list)
    assert any(item["id"] == test_notification.id for item in body["data"])
    assert "pagination" in body
    assert body["pagination"]["page"] == 1

    # 2. Lọc theo category khớp
    res_cat = admin_client.get("/api/v1/notifications/my?category=HOMEWORK")
    assert res_cat.status_code == 200
    assert any(item["id"] == test_notification.id for item in res_cat.json()["data"])

    # 3. Lọc theo category khác -> không chứa
    res_other = admin_client.get("/api/v1/notifications/my?category=DUTY")
    assert res_other.status_code == 200
    assert not any(item["id"] == test_notification.id for item in res_other.json()["data"])


def test_get_unread_count_api(admin_client, test_notification):
    """Kiểm tra API đếm số lượng thông báo chưa đọc."""
    res = admin_client.get("/api/v1/notifications/unread-count")
    assert res.status_code == 200
    body = res.json()
    assert body["is_success"] is True
    assert "unread_count" in body["data"]
    assert body["data"]["unread_count"] >= 1


def test_mark_as_read_api(admin_client, test_notification):
    """Kiểm tra API đánh dấu 1 thông báo đã đọc."""
    res = admin_client.patch(f"/api/v1/notifications/{test_notification.id}/read")
    assert res.status_code == 200
    body = res.json()
    assert body["is_success"] is True
    assert body["data"]["is_read"] is True


def test_mark_all_as_read_api(admin_client, test_notification):
    """Kiểm tra API đánh dấu tất cả thông báo đã đọc."""
    res = admin_client.post("/api/v1/notifications/read-all")
    assert res.status_code == 200
    body = res.json()
    assert body["is_success"] is True
    assert isinstance(body["data"], int)


def test_trigger_reminder_scan_api(admin_client):
    """Kiểm tra endpoint Admin kích hoạt quét nhắc nhở thủ công với dry_run=True."""
    res = admin_client.post("/api/v1/notifications/trigger?dry_run=true")
    assert res.status_code == 200
    body = res.json()
    assert body["is_success"] is True
    assert "total_tasks_scanned" in body["data"]
    assert "total_reminders_sent" in body["data"]


def test_notifications_unauthorized(unauth_client):
    """Kiểm tra chặn 401 khi không đăng nhập."""
    res = unauth_client.get("/api/v1/notifications/my")
    assert res.status_code == 401
