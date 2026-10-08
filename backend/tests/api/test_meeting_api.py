"""
API Tests for Meeting Controller (/api/v1/meetings).
Covers CRUD endpoints, check-in with card, form check-in, check-out, capacity status,
and evaluation endpoints for both success and error branches (401, 403, 404, 422).
"""

from datetime import datetime, timedelta
import io
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from sqlalchemy import text


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def test_meeting(admin_client, mock_current_user):
    """Tạo một meeting tạm để phục vụ các bài test và tự động dọn dẹp sau khi xong."""
    now = datetime.now()
    payload = {
        "title": f"API Test Meeting {uuid.uuid4().hex[:6]}",
        "content": "Test meeting for API coverage",
        "start_time": (now + timedelta(hours=2)).isoformat(),
        "end_time": (now + timedelta(hours=3)).isoformat(),
        "require_check_in": True,
        "enable_evaluation": True,
        "user_ids": [mock_current_user.id],
    }
    res = admin_client.post("/api/v1/meetings", json=payload)
    assert res.status_code == 201
    meeting_data = res.json()["data"]
    meeting_id = meeting_data["id"]

    yield meeting_data

    # Cleanup
    admin_client.delete(f"/api/v1/meetings/{meeting_id}")


@pytest.fixture
def active_meeting_for_checkin(admin_client, mock_current_user, db_session):
    """Tạo meeting diễn ra ngay bây giờ (±30 phút) để kiểm thử luồng Check-in."""
    now = datetime.now()
    payload = {
        "title": f"Check-in Active Meeting {uuid.uuid4().hex[:6]}",
        "content": "Active meeting for check-in test",
        "start_time": (now - timedelta(minutes=10)).isoformat(),
        "end_time": (now + timedelta(minutes=50)).isoformat(),
        "require_check_in": True,
        "enable_evaluation": False,
        "user_ids": [mock_current_user.id],
    }
    res = admin_client.post("/api/v1/meetings", json=payload)
    assert res.status_code == 201
    meeting_data = res.json()["data"]
    meeting_id = meeting_data["id"]

    yield meeting_data

    admin_client.delete(f"/api/v1/meetings/{meeting_id}")


# ---------------------------------------------------------------------------
# AVAILABLE SEATS & CAPACITY
# ---------------------------------------------------------------------------

def test_get_available_seats_unauthenticated(unauth_client):
    """Chưa đăng nhập truy cập available-seats trả về 401."""
    res = unauth_client.get("/api/v1/meetings/available-seats")
    assert res.status_code == 401


def test_get_available_seats_success(admin_client):
    """Admin lấy danh sách ghế khả dụng thành công."""
    res = admin_client.get("/api/v1/meetings/available-seats")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_get_available_seats_as_member(member_client):
    """Member thông thường cũng có thể xem ghế khả dụng."""
    res = member_client.get("/api/v1/meetings/available-seats")
    assert res.status_code == 200
    assert res.json()["is_success"] is True


def test_get_capacity_status_success(admin_client):
    """Lấy trạng thái capacity hiện tại."""
    res = admin_client.get("/api/v1/meetings/capacity/status")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert "current_count" in data["data"]


def test_get_capacity_forecast_success(admin_client):
    """Lấy dự báo capacity 30 phút tới."""
    res = admin_client.get("/api/v1/meetings/capacity/forecast")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert "current_count" in data["data"]


# ---------------------------------------------------------------------------
# CREATE MEETING
# ---------------------------------------------------------------------------

def test_create_meeting_unauthenticated(unauth_client):
    """Chưa đăng nhập không được phép tạo meeting (401)."""
    res = unauth_client.post("/api/v1/meetings", json={})
    assert res.status_code == 401


def test_create_meeting_as_member_returns_403(member_client):
    """Member không có quyền MeetingPermission.CREATE bị chặn 403 Forbidden."""
    now = datetime.now()
    payload = {
        "title": "Forbidden Meeting",
        "start_time": (now + timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
    }
    res = member_client.post("/api/v1/meetings", json=payload)
    assert res.status_code == 403


def test_create_meeting_missing_required_fields_returns_422(admin_client):
    """Tạo meeting thiếu các trường bắt buộc trả về 422."""
    res = admin_client.post("/api/v1/meetings", json={"title": "Missing Times"})
    assert res.status_code == 422


def test_create_meeting_as_admin_success(admin_client, mock_current_user):
    """Admin tạo meeting thành công (201 Created)."""
    now = datetime.now()
    payload = {
        "title": "Comprehensive Meeting Test",
        "content": "Detailed agenda",
        "start_time": (now + timedelta(hours=5)).isoformat(),
        "end_time": (now + timedelta(hours=6)).isoformat(),
        "require_check_in": True,
        "enable_evaluation": False,
        "user_ids": [mock_current_user.id],
    }
    res = admin_client.post("/api/v1/meetings", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["title"] == "Comprehensive Meeting Test"
    created_id = data["data"]["id"]

    # Dọn dẹp
    admin_client.delete(f"/api/v1/meetings/{created_id}")


# ---------------------------------------------------------------------------
# LIST & GET MEETING
# ---------------------------------------------------------------------------

def test_list_meetings_unauthenticated(unauth_client):
    """Chưa đăng nhập không được lấy danh sách meetings (401)."""
    res = unauth_client.get("/api/v1/meetings")
    assert res.status_code == 401


def test_list_meetings_as_member_returns_403(member_client):
    """Member không có MeetingPermission.READ bị chặn 403."""
    res = member_client.get("/api/v1/meetings")
    assert res.status_code == 403


def test_list_meetings_as_admin_success(admin_client, test_meeting):
    """Admin lấy danh sách meetings thành công kèm pagination/date filters."""
    res = admin_client.get("/api/v1/meetings?skip=0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert any(m["id"] == test_meeting["id"] for m in data["data"])


def test_get_meeting_detail_not_found(admin_client):
    """Truy vấn meeting không tồn tại trả về lỗi (400 hoặc 404)."""
    res = admin_client.get("/api/v1/meetings/99999999")
    assert res.status_code in (400, 404)


def test_get_meeting_detail_success(admin_client, test_meeting):
    """Admin lấy chi tiết meeting kèm danh sách participants."""
    res = admin_client.get(f"/api/v1/meetings/{test_meeting['id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["id"] == test_meeting["id"]
    assert "participants" in data["data"]


# ---------------------------------------------------------------------------
# UPDATE MEETING & PARTICIPANT STATUS
# ---------------------------------------------------------------------------

def test_update_meeting_as_member_returns_403(member_client, test_meeting):
    """Member không có quyền sửa meeting (403 Forbidden)."""
    payload = {"title": "Attempted update"}
    res = member_client.put(f"/api/v1/meetings/{test_meeting['id']}", json=payload)
    assert res.status_code == 403


def test_update_meeting_not_found(admin_client):
    """Cập nhật meeting không tồn tại trả về lỗi."""
    payload = {"title": "Ghost update"}
    res = admin_client.put("/api/v1/meetings/99999999", json=payload)
    assert res.status_code in (400, 404)


def test_update_meeting_success(admin_client, test_meeting):
    """Admin cập nhật thông tin meeting thành công."""
    payload = {"title": "Updated Title Meeting", "content": "Updated content"}
    res = admin_client.put(f"/api/v1/meetings/{test_meeting['id']}", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["title"] == "Updated Title Meeting"


def test_update_participant_status_success(admin_client, test_meeting, mock_current_user):
    """Admin cập nhật thủ công trạng thái của một người tham gia meeting."""
    payload = {
        "status": "JOINED",
        "check_in_at": datetime.now().isoformat(),
    }
    res = admin_client.put(
        f"/api/v1/meetings/{test_meeting['id']}/participants/{mock_current_user.id}/status",
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert data["data"]["user_id"] == mock_current_user.id
    assert data["data"]["status"] == "JOINED"


def test_update_participant_status_not_found(admin_client, test_meeting):
    """Cập nhật participant không tồn tại trả về lỗi."""
    payload = {"status": "JOINED"}
    res = admin_client.put(
        f"/api/v1/meetings/{test_meeting['id']}/participants/99999999/status",
        json=payload,
    )
    assert res.status_code in (400, 404)


# ---------------------------------------------------------------------------
# CHECK-IN WITH CARD (RFID/CARD CODE)
# ---------------------------------------------------------------------------

def test_check_in_with_card_unauthenticated(unauth_client):
    """Endpoint quẹt thẻ yêu cầu quyền MeetingPermission.CHECK_IN (401 khi chưa login)."""
    res = unauth_client.post("/api/v1/meetings/check-in-with-card", json={"card_code": "CARD_123"})
    assert res.status_code == 401


def test_check_in_with_card_unregistered(admin_client):
    """Quẹt mã thẻ chưa đăng ký trong hệ thống."""
    res = admin_client.post(
        "/api/v1/meetings/check-in-with-card",
        json={"card_code": "NON_EXISTENT_CARD_999999"},
    )
    assert res.status_code == 200
    assert "X-Message" in res.headers
    assert "The chua duoc dang ky" in res.headers["X-Message"]


def test_check_in_with_card_no_meeting(admin_client, db_engine, mock_current_user):
    """User có thẻ nhưng không có cuộc họp nào trong vòng 30 phút."""
    card_code = f"CARD_NOMEET_{uuid.uuid4().hex[:6]}"
    with db_engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET check_in_card_code = :card WHERE id = :uid"),
            {"card": card_code, "uid": mock_current_user.id},
        )
        conn.commit()

    res = admin_client.post(
        "/api/v1/meetings/check-in-with-card",
        json={"card_code": card_code},
    )
    assert res.status_code == 200
    assert "X-Message" in res.headers
    assert "khong co buoi hop nao" in res.headers["X-Message"]


def test_check_in_with_card_success_flow(
    admin_client, db_engine, mock_current_user, active_meeting_for_checkin
):
    """Quẹt thẻ thành công và quẹt lại lần 2 báo đã điểm danh."""
    card_code = f"CARD_FLOW_{uuid.uuid4().hex[:6]}"
    with db_engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET check_in_card_code = :card WHERE id = :uid"),
            {"card": card_code, "uid": mock_current_user.id},
        )
        conn.commit()

    # Quẹt lần 1: Thành công
    res1 = admin_client.post(
        "/api/v1/meetings/check-in-with-card",
        json={"card_code": card_code},
    )
    assert res1.status_code == 200
    assert "X-Message" in res1.headers
    assert "diem danh thanh cong" in res1.headers["X-Message"]

    # Quẹt lần 2: Đã điểm danh rồi
    res2 = admin_client.post(
        "/api/v1/meetings/check-in-with-card",
        json={"card_code": card_code},
    )
    assert res2.status_code == 200
    assert "X-Message" in res2.headers
    assert "da diem danh cho buoi hop" in res2.headers["X-Message"]


# ---------------------------------------------------------------------------
# CHECK-IN (FORM & FILE) AND CHECK-OUT
# ---------------------------------------------------------------------------

@patch("app.shared.infrastructure.minio_service.MinioService.upload_file", new_callable=AsyncMock)
def test_check_in_form_success(
    mock_upload, admin_client, mock_current_user, active_meeting_for_checkin
):
    """Điểm danh gửi form user_ids kèm upload ảnh (MinIO được mock)."""
    mock_upload.return_value = "https://minio.test/checkin_image.jpg"
    fake_image = io.BytesIO(b"fake-image-bytes")

    data = {
        "user_ids": [mock_current_user.id],
    }
    files = {
        "image": ("checkin.jpg", fake_image, "image/jpeg"),
    }
    res = admin_client.post("/api/v1/meetings/check-in", data=data, files=files)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["is_success"] is True
    assert isinstance(res_data["data"], list)


def test_check_out_not_checked_in_returns_400(
    admin_client, mock_current_user, active_meeting_for_checkin
):
    """Chưa check-in mà thực hiện check-out trả về lỗi 400 Bad Request."""
    payload = {
        "user_id": mock_current_user.id,
        "client_time": datetime.now().isoformat(),
    }
    res = admin_client.post("/api/v1/meetings/check-out", json=payload)
    assert res.status_code == 400
    err_text = res.json().get("message") or res.json().get("detail") or ""
    assert "Không tìm thấy buổi họp nào đang tham gia" in err_text


def test_check_out_success(
    admin_client, mock_current_user, active_meeting_for_checkin
):
    """Check-out khỏi buổi họp thành công sau khi đã điểm danh."""
    # Bước 1: Set trạng thái sang JOINED có check_in_at
    admin_client.put(
        f"/api/v1/meetings/{active_meeting_for_checkin['id']}/participants/{mock_current_user.id}/status",
        json={"status": "JOINED", "check_in_at": datetime.now().isoformat()},
    )

    # Bước 2: Thực hiện check-out
    payload = {
        "user_id": mock_current_user.id,
        "client_time": datetime.now().isoformat(),
    }
    res = admin_client.post("/api/v1/meetings/check-out", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["is_success"] is True


# ---------------------------------------------------------------------------
# EVALUATIONS & DELETE
# ---------------------------------------------------------------------------

def test_get_meeting_evaluation_summary(admin_client, test_meeting):
    """Lấy báo cáo tổng hợp kết quả đánh giá của buổi học."""
    res = admin_client.get(f"/api/v1/meetings/{test_meeting['id']}/evaluations/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert "total_evaluations" in data["data"]


def test_get_my_evaluation_result_locked_without_review(admin_client, test_meeting):
    """Khi chưa hoàn thành đánh giá Trainer, Trainee bị khóa xem kết quả (403 Forbidden)."""
    res = admin_client.get(f"/api/v1/meetings/{test_meeting['id']}/evaluations/my-result")
    assert res.status_code == 403
    err_text = res.json().get("message") or res.json().get("detail") or ""
    assert "Bạn cần hoàn thành đánh giá Trainer" in err_text


def test_get_my_evaluation_result_disabled_evaluation(admin_client, mock_current_user):
    """Meeting không kích hoạt đánh giá trả về null (200 OK)."""
    now = datetime.now()
    payload = {
        "title": "Meeting No Eval",
        "start_time": (now + timedelta(hours=3)).isoformat(),
        "end_time": (now + timedelta(hours=4)).isoformat(),
        "enable_evaluation": False,
        "user_ids": [mock_current_user.id],
    }
    create_res = admin_client.post("/api/v1/meetings", json=payload)
    meeting_id = create_res.json()["data"]["id"]

    try:
        res = admin_client.get(f"/api/v1/meetings/{meeting_id}/evaluations/my-result")
        assert res.status_code == 200
        assert res.json()["data"] is None
    finally:
        admin_client.delete(f"/api/v1/meetings/{meeting_id}")


def test_submit_evaluation_before_start_returns_400(admin_client, test_meeting, mock_current_user):
    """Buổi học chưa bắt đầu không thể gửi đánh giá (400 Bad Request)."""
    payload = {
        "target_user_id": mock_current_user.id,
        "scores": [{"criteria_code": "ATTENDANCE_CONDUCT", "score": 5}],
    }
    res = admin_client.post(
        f"/api/v1/meetings/{test_meeting['id']}/evaluations/trainer",
        json=payload,
    )
    assert res.status_code == 400
    err_text = res.json().get("message") or res.json().get("detail") or ""
    assert "chưa bắt đầu" in err_text


def test_submit_trainer_evaluation_success(admin_client, mock_current_user):
    """Trainer gửi đánh giá học viên thành công sau khi buổi học bắt đầu."""
    now = datetime.now()
    payload_m = {
        "title": f"Started Meeting {uuid.uuid4().hex[:6]}",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
        "enable_evaluation": True,
        "user_ids": [mock_current_user.id],
    }
    create_res = admin_client.post("/api/v1/meetings", json=payload_m)
    meeting_id = create_res.json()["data"]["id"]

    try:
        payload = {
            "target_user_id": mock_current_user.id,
            "scores": [
                {"criteria_code": "ATTENDANCE_CONDUCT", "score": 5},
                {"criteria_code": "INTERACTION_CONTRIBUTION", "score": 4},
            ],
            "feedback_text": "Học viên tham gia tích cực",
        }
        res = admin_client.post(
            f"/api/v1/meetings/{meeting_id}/evaluations/trainer",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["is_success"] is True
        assert data["data"]["average_score"] == 4.5
    finally:
        admin_client.delete(f"/api/v1/meetings/{meeting_id}")


def test_submit_trainee_evaluation_success(admin_client, mock_current_user):
    """Trainee gửi đánh giá buổi học và Trainer thành công sau khi bắt đầu."""
    now = datetime.now()
    payload_m = {
        "title": f"Started Meeting {uuid.uuid4().hex[:6]}",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
        "enable_evaluation": True,
        "user_ids": [mock_current_user.id],
    }
    create_res = admin_client.post("/api/v1/meetings", json=payload_m)
    meeting_id = create_res.json()["data"]["id"]

    try:
        # Bước 1: Trainee cập nhật trạng thái đã tham gia (JOINED)
        admin_client.put(
            f"/api/v1/meetings/{meeting_id}/participants/{mock_current_user.id}/status",
            json={"status": "JOINED"},
        )

        # Bước 2: Gửi đánh giá Trainer
        payload = {
            "target_user_id": mock_current_user.id,
            "is_anonymous": True,
            "scores": [
                {"criteria_code": "CONTENT_QUALITY", "score": 5},
                {"criteria_code": "TEACHING_METHOD", "score": 5},
            ],
            "feedback_text": "Nội dung bài học rất hay và dễ hiểu",
        }
        res = admin_client.post(
            f"/api/v1/meetings/{meeting_id}/evaluations/trainee",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["is_success"] is True
        assert data["data"]["is_anonymous"] is True
    finally:
        admin_client.delete(f"/api/v1/meetings/{meeting_id}")


def test_delete_meeting_as_member_returns_403(member_client, test_meeting):
    """Member không có quyền xoá meeting (403 Forbidden)."""
    res = member_client.delete(f"/api/v1/meetings/{test_meeting['id']}")
    assert res.status_code == 403


def test_delete_meeting_not_found(admin_client):
    """Xóa meeting không tồn tại trả về lỗi."""
    res = admin_client.delete("/api/v1/meetings/99999999")
    assert res.status_code in (400, 404)


def test_delete_meeting_success(admin_client, mock_current_user):
    """Admin xóa meeting thành công."""
    now = datetime.now()
    payload = {
        "title": "Meeting to Delete",
        "start_time": (now + timedelta(hours=10)).isoformat(),
        "end_time": (now + timedelta(hours=11)).isoformat(),
        "user_ids": [mock_current_user.id],
    }
    res = admin_client.post("/api/v1/meetings", json=payload)
    assert res.status_code == 201
    meeting_id = res.json()["data"]["id"]

    del_res = admin_client.delete(f"/api/v1/meetings/{meeting_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_success"] is True
