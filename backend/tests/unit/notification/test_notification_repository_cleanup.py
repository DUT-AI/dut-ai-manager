from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.reminder.domain.entity import (
    Notification,
)
from app.reminder.infrastructure.repository import NotificationRepository


def test_notification_repository_deletion_and_cleanup(db_session: Session, mock_current_user):
    repo = NotificationRepository(db_session)
    user_id = mock_current_user.id

    # Lấy hoặc tạo 1 user khác hợp lệ trong DB để test ownership
    from app.user.infrastructure.model import UserModel
    other_user = db_session.query(UserModel).filter(UserModel.id != user_id).first()
    if not other_user:
        other_user = UserModel(
            name="Other User For Test",
            email="other_user_test@example.com",
            status="ACTIVE",
        )
        db_session.add(other_user)
        db_session.commit()
    other_user_id = other_user.id

    now = datetime.now(UTC)

    # 1. Tạo 4 notification:
    # n1: user_id, is_read=False, created_at=now
    # n2: user_id, is_read=True, created_at=now
    # n3: other_user_id, is_read=True, created_at=now
    # n4: user_id, is_read=True, created_at=now - 40 days (cũ)
    n1 = repo.add(Notification(
        user_id=user_id,
        title="N1 Unread",
        content="Content 1",
        is_read=False,
    ))
    n2 = repo.add(Notification(
        user_id=user_id,
        title="N2 Read",
        content="Content 2",
        is_read=True,
        read_at=now,
    ))
    n3 = repo.add(Notification(
        user_id=other_user_id,
        title="N3 Other User",
        content="Content 3",
        is_read=True,
        read_at=now,
    ))
    n4 = repo.add(Notification(
        user_id=user_id,
        title="N4 Expired Read",
        content="Content 4",
        is_read=True,
        read_at=now - timedelta(days=40),
    ))

    # Cập nhật created_at của n4 để giả lập bản ghi cũ 40 ngày
    with db_session.begin_nested():
        from app.reminder.infrastructure.model import NotificationModel
        model_n4 = db_session.get(NotificationModel, n4.id)
        if model_n4:
            model_n4.created_at = now - timedelta(days=40)
            db_session.flush()

    try:
        # Test delete_by_id_and_user
        # User khác cố tình xóa n1 -> False
        assert repo.delete_by_id_and_user(n1.id, other_user_id) is False
        # Chính chủ xóa n1 -> True
        assert repo.delete_by_id_and_user(n1.id, user_id) is True
        # Sau khi xóa n1, n1 không còn
        assert repo.get_by_id(n1.id) is None

        # Test delete_read_before (TTL Housekeeping)
        cutoff = now - timedelta(days=30)
        deleted_expired = repo.delete_read_before(cutoff)
        assert deleted_expired >= 1
        assert repo.get_by_id(n4.id) is None
        # n2 (mới đọc hôm nay) không bị xóa bởi housekeeping
        assert repo.get_by_id(n2.id) is not None

        # Test delete_read_by_user
        deleted_count = repo.delete_read_by_user(user_id)
        assert deleted_count >= 1
        assert repo.get_by_id(n2.id) is None
        # n3 của other_user_id vẫn còn nguyên
        assert repo.get_by_id(n3.id) is not None

    finally:
        # Dọn dẹp n3
        repo.delete_by_id_and_user(n3.id, other_user_id)
