"""
API Tests for Homework Controller (/api/v1/homeworks).
Covers CRUD endpoints, reports, submission status, Quiz webhooks, user submission audit logs,
and sync from Quiz for both success and error branches (401, 403, 404, 422).
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import uuid
import pytest

from app.core.config import settings


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_quiz_api_metadata():
    """Mock QuizApiClient.get_lesson_metadata để không phụ thuộc Quiz network API."""
    with patch(
        "app.homework.infrastructure.quiz_api.QuizApiClient.get_lesson_metadata",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = {
            "name": "Mocked Quiz Lesson",
            "has_coding": True,
            "has_game": True,
        }
        yield mock_get


@pytest.fixture
def test_homework(admin_client, mock_current_user):
    """Tạo một bài tập tạm thời và dọn dẹp sau khi kiểm thử xong."""
    unique_slug = f"test-slug-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": f"API Test Homework {uuid.uuid4().hex[:6]}",
        "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
        "link": f"https://quiz.example.com/lessons/{unique_slug}",
        "slug": unique_slug,
        "requires_coding": True,
        "requires_game": True,
        "assignee_ids": [mock_current_user.id],
    }
    res = admin_client.post("/api/v1/homeworks", json=payload)
    assert res.status_code == 200
    hw_data = res.json()["data"]
    hw_id = hw_data["id"]

    yield hw_data

    # Cleanup: Hard delete or soft delete
    admin_client.delete(f"/api/v1/homeworks/{hw_id}")


# ---------------------------------------------------------------------------
# LIST & GET HOMEWORKS
# ---------------------------------------------------------------------------

def test_list_homeworks_unauthenticated(unauth_client):
    """Chưa đăng nhập khi lấy danh sách bài tập trả về 401."""
    res = unauth_client.get("/api/v1/homeworks")
    assert res.status_code == 401


def test_list_homeworks_as_member_returns_403(member_client):
    """Member không có HomeworkPermission.READ bị chặn 403 Forbidden."""
    res = member_client.get("/api/v1/homeworks")
    assert res.status_code == 403


def test_list_homeworks_as_admin_success(admin_client, test_homework):
    """Admin lấy danh sách bài tập thành công."""
    res = admin_client.get("/api/v1/homeworks?skip=0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert any(h["id"] == test_homework["id"] for h in data["data"])


def test_get_my_homeworks_success(admin_client):
    """Lấy danh sách bài tập được giao cho current user."""
    res = admin_client.get("/api/v1/homeworks/me")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_rescan_all_homeworks_dry_run(admin_client):
    """Admin quét lại toàn bộ bài tập ở chế độ dry-run an toàn."""
    res = admin_client.post("/api/v1/homeworks/admin/rescan-all?dry_run=true")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["dry_run"] is True


# ---------------------------------------------------------------------------
# CREATE HOMEWORK
# ---------------------------------------------------------------------------

def test_create_homework_unauthenticated(unauth_client):
    """Chưa đăng nhập không được tạo bài tập (401)."""
    res = unauth_client.post("/api/v1/homeworks", json={})
    assert res.status_code == 401


def test_create_homework_as_member_returns_403(member_client):
    """Member không có HomeworkPermission.CREATE bị chặn 403."""
    payload = {
        "title": "Forbidden Homework",
        "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
    }
    res = member_client.post("/api/v1/homeworks", json=payload)
    assert res.status_code == 403


def test_create_homework_missing_required_fields_returns_422(admin_client):
    """Thiếu các trường bắt buộc (title, deadline) trả về 422."""
    res = admin_client.post("/api/v1/homeworks", json={"title": "Missing Deadline"})
    assert res.status_code == 422


def test_create_homework_no_requirement_returns_400(admin_client):
    """Không chọn yêu cầu coding hoặc game trả về 400 Bad Request."""
    payload = {
        "title": "Invalid Homework Requirement",
        "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
        "slug": "some-slug",
        "requires_coding": False,
        "requires_game": False,
    }
    res = admin_client.post("/api/v1/homeworks", json=payload)
    assert res.status_code == 400
    err_text = res.json().get("message") or res.json().get("detail") or ""
    assert "chọn ít nhất một yêu cầu" in err_text


def test_create_homework_slug_not_found_in_quiz_returns_400(admin_client):
    """Slug bài học không tồn tại trên Quiz API trả về 400."""
    with patch(
        "app.homework.infrastructure.quiz_api.QuizApiClient.get_lesson_metadata",
        new_callable=AsyncMock,
        return_value=None,
    ):
        payload = {
            "title": "Non-existent Quiz Lesson",
            "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
            "slug": "ghost-slug",
            "requires_coding": True,
        }
        res = admin_client.post("/api/v1/homeworks", json=payload)
        assert res.status_code == 400
        err_text = res.json().get("message") or res.json().get("detail") or ""
        assert "không tồn tại trên hệ thống Quiz" in err_text


def test_create_homework_as_admin_success(admin_client, mock_current_user):
    """Admin tạo bài tập thành công."""
    slug = f"hw-{uuid.uuid4().hex[:6]}"
    payload = {
        "title": "Admin Created Homework",
        "deadline": (datetime.now() + timedelta(days=5)).isoformat(),
        "slug": slug,
        "requires_coding": True,
        "requires_game": False,
        "assignee_ids": [mock_current_user.id],
    }
    res = admin_client.post("/api/v1/homeworks", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["title"] == "Admin Created Homework"
    hw_id = data["data"]["id"]

    # Cleanup
    admin_client.delete(f"/api/v1/homeworks/{hw_id}")


# ---------------------------------------------------------------------------
# REPORTS & DETAIL
# ---------------------------------------------------------------------------

def test_get_unsubmitted_report(admin_client):
    """Thống kê bài tập chưa nộp của toàn bộ user."""
    res = admin_client.get("/api/v1/homeworks/report/unsubmitted")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_unsubmitted_by_user(admin_client, mock_current_user):
    """Lấy danh sách bài tập chưa nộp của một user cụ thể."""
    res = admin_client.get(f"/api/v1/homeworks/report/unsubmitted/{mock_current_user.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_homework_detail_not_found(admin_client):
    """Chi tiết bài tập không tồn tại trả về 404."""
    res = admin_client.get("/api/v1/homeworks/99999999")
    assert res.status_code == 404


def test_get_homework_detail_success(admin_client, test_homework):
    """Lấy chi tiết bài tập theo ID thành công."""
    res = admin_client.get(f"/api/v1/homeworks/{test_homework['id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["id"] == test_homework["id"]


def test_get_homework_submission_status_not_found(admin_client):
    """Trạng thái nộp bài với bài tập không tồn tại trả về 404."""
    res = admin_client.get("/api/v1/homeworks/99999999/submission-status")
    assert res.status_code == 404


def test_get_homework_submission_status_success(admin_client, test_homework):
    """Lấy trạng thái nộp bài (coding/game) của một bài tập."""
    res = admin_client.get(f"/api/v1/homeworks/{test_homework['id']}/submission-status")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert "coding" in data["data"]
    assert "game" in data["data"]


# ---------------------------------------------------------------------------
# UPDATE, DELETE & RESTORE
# ---------------------------------------------------------------------------

def test_update_homework_as_member_returns_403(member_client, test_homework):
    """Member không có quyền sửa bài tập (403 Forbidden)."""
    payload = {"title": "Member updated"}
    res = member_client.put(f"/api/v1/homeworks/{test_homework['id']}", json=payload)
    assert res.status_code == 403


def test_update_homework_not_found(admin_client):
    """Cập nhật bài tập không tồn tại trả về 404."""
    payload = {"title": "Ghost update"}
    res = admin_client.put("/api/v1/homeworks/99999999", json=payload)
    assert res.status_code == 404


def test_update_homework_success(admin_client, test_homework):
    """Cập nhật thông tin bài tập thành công."""
    payload = {
        "title": "Updated Homework Title",
        "requires_game": False,
    }
    res = admin_client.put(f"/api/v1/homeworks/{test_homework['id']}", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["title"] == "Updated Homework Title"


def test_delete_homework_as_member_returns_403(member_client, test_homework):
    """Member không có quyền xóa bài tập (403 Forbidden)."""
    res = member_client.delete(f"/api/v1/homeworks/{test_homework['id']}")
    assert res.status_code == 403


def test_delete_homework_not_found(admin_client):
    """Xóa bài tập không tồn tại trả về 404."""
    res = admin_client.delete("/api/v1/homeworks/99999999")
    assert res.status_code == 404


def test_delete_and_restore_homework_flow(admin_client, mock_current_user):
    """Quy trình Xóa mềm và Khôi phục (restore) bài tập."""
    payload = {
        "title": "Homework for Delete and Restore",
        "deadline": (datetime.now() + timedelta(days=2)).isoformat(),
        "slug": f"del-res-{uuid.uuid4().hex[:6]}",
        "requires_coding": True,
        "assignee_ids": [mock_current_user.id],
    }
    create_res = admin_client.post("/api/v1/homeworks", json=payload)
    hw_id = create_res.json()["data"]["id"]

    # 1. Xóa bài tập
    del_res = admin_client.delete(f"/api/v1/homeworks/{hw_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_success"] is True

    # 2. Khôi phục bài tập
    res_restore = admin_client.put(f"/api/v1/homeworks/{hw_id}/restore")
    assert res_restore.status_code == 200
    assert res_restore.json()["is_success"] is True
    assert res_restore.json()["data"]["id"] == hw_id

    # 3. Dọn dẹp lại sau test
    admin_client.delete(f"/api/v1/homeworks/{hw_id}")


def test_restore_homework_not_found(admin_client):
    """Khôi phục bài tập không tồn tại trả về 404."""
    res = admin_client.put("/api/v1/homeworks/99999999/restore")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# QUIZ WEBHOOK & SUBMISSIONS AUDIT LOG
# ---------------------------------------------------------------------------

def test_receive_submission_webhook_invalid_secret_returns_401(admin_client, test_homework):
    """Gửi webhook không có hoặc sai header X-Webhook-Secret trả về 401."""
    payload = {
        "lesson_slug": test_homework["slug"],
        "user_id": 1,
        "type": "CODING",
        "submitted_at": datetime.now().isoformat(),
        "is_passed": True,
    }
    # Trường hợp không có header
    res1 = admin_client.post("/api/v1/homeworks/webhook/submission", json=payload)
    assert res1.status_code == 401

    # Trường hợp sai header
    headers = {"X-Webhook-Secret": "WRONG_SECRET_12345"}
    res2 = admin_client.post("/api/v1/homeworks/webhook/submission", json=payload, headers=headers)
    assert res2.status_code == 401


def test_receive_submission_webhook_success_coding(admin_client, test_homework, mock_current_user):
    """Quiz webhook ghi nhận nộp bài Coding hợp lệ từ hệ thống Quiz."""
    headers = {"X-Webhook-Secret": settings.QUIZ_WEBHOOK_SECRET}
    payload = {
        "lesson_slug": test_homework["slug"],
        "user_id": mock_current_user.id,
        "type": "CODING",
        "submitted_at": datetime.now().isoformat(),
        "is_passed": True,
        "score": 10.0,
        "exercise_id": "exercise_01",
        "exercise_title": "Viết thuật toán tìm kiếm",
        "attempt_number": 1,
        "details": {"test_cases_passed": 5, "total_test_cases": 5},
    }
    res = admin_client.post("/api/v1/homeworks/webhook/submission", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_receive_submission_webhook_success_game(admin_client, test_homework, mock_current_user):
    """Quiz webhook ghi nhận hoàn thành bài tập Game hợp lệ."""
    headers = {"X-Webhook-Secret": settings.QUIZ_WEBHOOK_SECRET}
    payload = {
        "lesson_slug": test_homework["slug"],
        "user_id": mock_current_user.id,
        "type": "GAME",
        "submitted_at": datetime.now().isoformat(),
        "is_passed": True,
        "score": 95.0,
        "details": {"level": 3, "time_spent_seconds": 120},
    }
    res = admin_client.post("/api/v1/homeworks/webhook/submission", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True


def test_get_my_homework_submissions(admin_client, test_homework):
    """Lấy lịch sử tất cả các lần nộp bài của chính học viên hiện tại."""
    res = admin_client.get(f"/api/v1/homeworks/{test_homework['id']}/my-submissions")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_user_homework_submissions(admin_client, test_homework, mock_current_user):
    """Admin lấy lịch sử tất cả các lần nộp bài của một học viên cụ thể."""
    res = admin_client.get(
        f"/api/v1/homeworks/{test_homework['id']}/users/{mock_current_user.id}/submissions"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


@patch("app.homework.infrastructure.quiz_api.QuizApiClient.get_homework_submissions_for_sync", new_callable=AsyncMock)
def test_sync_homework_from_quiz_success(mock_quiz_sync, admin_client, test_homework):
    """Đồng bộ bài nộp từ Quiz API cho bài tập (mock API ngoài)."""
    mock_quiz_sync.return_value = []
    res = admin_client.post(f"/api/v1/homeworks/{test_homework['id']}/sync")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
