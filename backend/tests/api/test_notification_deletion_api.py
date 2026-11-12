from datetime import UTC, datetime

from app.reminder.domain.entity import (
    Notification,
)
from app.reminder.infrastructure.repository import NotificationRepository


def test_notification_deletion_api_flows(admin_client, db_session, mock_current_user):
    repo = NotificationRepository(db_session)
    user_id = mock_current_user.id

    from app.user.infrastructure.model import UserModel
    other_user = db_session.query(UserModel).filter(UserModel.id != user_id).first()
    assert other_user is not None, "Cần có user thứ hai trong DB"
    other_user_id = other_user.id

    now = datetime.now(UTC)

    # 1. Tạo các thông báo cho test
    # n1: Của user_id, chưa đọc
    n1 = repo.add(Notification(
        user_id=user_id,
        title="My Unread Notification",
        content="Testing delete",
        is_read=False,
    ))
    # n2: Của user_id, đã đọc
    n2 = repo.add(Notification(
        user_id=user_id,
        title="My Read Notification 1",
        content="Testing read-all delete 1",
        is_read=True,
        read_at=now,
    ))
    # n3: Của user_id, đã đọc
    n3 = repo.add(Notification(
        user_id=user_id,
        title="My Read Notification 2",
        content="Testing read-all delete 2",
        is_read=True,
        read_at=now,
    ))
    # n4: Của other_user_id, đã đọc
    n4 = repo.add(Notification(
        user_id=other_user_id,
        title="Other User Read Notification",
        content="Should not be deleted",
        is_read=True,
        read_at=now,
    ))
    db_session.commit()

    try:
        # A. Test DELETE /api/v1/notifications/{id}
        # 1. Không thể xóa thông báo của người khác (404)
        res_other = admin_client.delete(f"/api/v1/notifications/{n4.id}")
        assert res_other.status_code == 404

        # 2. Xóa thông báo của chính mình thành công (200)
        res_own = admin_client.delete(f"/api/v1/notifications/{n1.id}")
        assert res_own.status_code == 200
        assert res_own.json()["data"] is True
        assert repo.get_by_id(n1.id) is None

        # 3. Xóa lại lần 2 -> 404
        res_again = admin_client.delete(f"/api/v1/notifications/{n1.id}")
        assert res_again.status_code == 404

        # B. Test DELETE /api/v1/notifications/read-all
        res_read_all = admin_client.delete("/api/v1/notifications/read-all")
        assert res_read_all.status_code == 200
        deleted_count = res_read_all.json()["data"]
        assert deleted_count >= 2
        assert repo.get_by_id(n2.id) is None
        assert repo.get_by_id(n3.id) is None

        # Thông báo của other_user_id vẫn còn nguyên vẹn
        assert repo.get_by_id(n4.id) is not None

        # C. Test POST /api/v1/notifications/housekeeping
        res_hk = admin_client.post("/api/v1/notifications/housekeeping?retention_days=30")
        assert res_hk.status_code == 200
        assert isinstance(res_hk.json()["data"], int)

    finally:
        # Dọn dẹp n4
        repo.delete_by_id_and_user(n4.id, other_user_id)
        db_session.commit()
