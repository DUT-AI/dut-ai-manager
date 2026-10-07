from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import text


def test_api_available_seats_endpoint(api_client):
    """Kiểm thử endpoint lấy danh sách buổi họp sắp tới kèm số ghế khả dụng."""
    res = api_client.get("/api/v1/meetings/available-seats")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)


def test_api_change_meeting_full_flow(api_client, mock_current_user, db_engine):
    """
    Kiểm thử trọn vẹn luồng đổi buổi họp qua API:
    - User đang ở Meeting A, có đơn xin vắng cũ
    - Gọi API POST /api/v1/permissions để đổi sang Meeting B
    - Kiểm tra: User bị rút khỏi A, thêm vào B, đơn vắng cũ bị huỷ, đơn đổi ca mới được tạo.
    """
    user_id = mock_current_user.id
    now = datetime.now(timezone.utc)
    start_a = now + timedelta(days=10)
    end_a = start_a + timedelta(hours=2)
    start_b = now + timedelta(days=11)
    end_b = start_b + timedelta(hours=2)

    meeting_a_id = None
    meeting_b_id = None
    old_perm_id = None

    try:
        # 1. Chuẩn bị dữ liệu test trên DB
        with db_engine.begin() as conn:
            res_a = conn.execute(
                text("""
                    INSERT INTO meetings (title, content, start_time, end_time, is_deleted, created_at, updated_at)
                    VALUES ('Test API Meeting A', 'Content A', :start_a, :end_a, false, NOW(), NOW())
                    RETURNING id
                """),
                {"start_a": start_a, "end_a": end_a},
            )
            meeting_a_id = res_a.scalar()

            res_b = conn.execute(
                text("""
                    INSERT INTO meetings (title, content, start_time, end_time, is_deleted, created_at, updated_at)
                    VALUES ('Test API Meeting B', 'Content B', :start_b, :end_b, false, NOW(), NOW())
                    RETURNING id
                """),
                {"start_b": start_b, "end_b": end_b},
            )
            meeting_b_id = res_b.scalar()

            # Thêm user vào Meeting A
            conn.execute(
                text("""
                    INSERT INTO meeting_participants (meeting_id, user_id, status, is_deleted, created_at, updated_at)
                    VALUES (:meeting_id, :user_id, 'NOT_JOINED', false, NOW(), NOW())
                """),
                {"meeting_id": meeting_a_id, "user_id": user_id},
            )

            # Tạo đơn xin vắng cũ tại Meeting A
            res_perm = conn.execute(
                text("""
                    INSERT INTO permission_requests (created_by, meeting_id, category, note, is_deleted, created_at, updated_at)
                    VALUES (:user_id, :meeting_id, 'ABSENCE', 'Don xin vang cu', false, NOW(), NOW())
                    RETURNING id
                """),
                {"user_id": user_id, "meeting_id": meeting_a_id},
            )
            old_perm_id = res_perm.scalar()

        # 2. Gọi POST /api/v1/permissions để đổi từ A sang B
        payload = {
            "category": "CHANGE_MEETING",
            "meeting_id": meeting_b_id,
            "old_meeting_id": meeting_a_id,
            "note": "Xin doi ca tu A sang B (API Test)",
        }
        res = api_client.post("/api/v1/permissions", json=payload)
        assert res.status_code == 200, f"Error: {res.json()}"
        res_data = res.json()
        assert res_data["is_success"] is True
        assert res_data["data"]["old_meeting_id"] == meeting_a_id
        assert res_data["data"]["meeting_id"] == meeting_b_id

        # 3. Kiểm tra DB state sau khi đổi ca
        with db_engine.connect() as conn:
            # User đã bị rút khỏi Meeting A
            in_a = conn.execute(
                text("""
                    SELECT count(*) FROM meeting_participants 
                    WHERE meeting_id = :mid AND user_id = :uid AND is_deleted = false
                """),
                {"mid": meeting_a_id, "uid": user_id},
            ).scalar()
            assert in_a == 0

            # User đã được thêm vào Meeting B
            in_b = conn.execute(
                text("""
                    SELECT count(*) FROM meeting_participants 
                    WHERE meeting_id = :mid AND user_id = :uid AND is_deleted = false
                """),
                {"mid": meeting_b_id, "uid": user_id},
            ).scalar()
            assert in_b == 1

            # Đơn xin vắng cũ đã được đánh dấu xoá
            old_perm_deleted = conn.execute(
                text("SELECT is_deleted FROM permission_requests WHERE id = :id"),
                {"id": old_perm_id},
            ).scalar()
            assert old_perm_deleted is True

    finally:
        # 4. Cleanup dữ liệu test
        with db_engine.begin() as conn:
            if meeting_a_id and meeting_b_id:
                conn.execute(
                    text("DELETE FROM permission_requests WHERE meeting_id IN (:ma, :mb) OR id = :pid"),
                    {"ma": meeting_a_id, "mb": meeting_b_id, "pid": old_perm_id or 0},
                )
                conn.execute(
                    text("DELETE FROM meeting_participants WHERE meeting_id IN (:ma, :mb)"),
                    {"ma": meeting_a_id, "mb": meeting_b_id},
                )
                conn.execute(
                    text("DELETE FROM meetings WHERE id IN (:ma, :mb)"),
                    {"ma": meeting_a_id, "mb": meeting_b_id},
                )


def test_api_change_meeting_validation_errors(api_client):
    """Kiểm thử validation lỗi nghiệp vụ trả về đúng HTTP 400."""
    # 1. Thiếu meeting_id
    res1 = api_client.post("/api/v1/permissions", json={"category": "CHANGE_MEETING", "note": "Test"})
    assert res1.status_code == 400
    assert "Vui lòng chọn buổi họp đích" in res1.json()["message"]

    # 2. Trùng meeting_id với old_meeting_id
    res2 = api_client.post(
        "/api/v1/permissions",
        json={"category": "CHANGE_MEETING", "meeting_id": 99999, "old_meeting_id": 99999, "note": "Test"},
    )
    assert res2.status_code == 400
    assert "Không thể đổi sang cùng một buổi họp" in res2.json()["message"]
