"""
Integration tests for Task Deadline Reminder & Unified Notification System.
Tests deduplication, cooldown, and notification repository operations on single unified table.
"""

from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.reminder.domain.entity import (
    Notification,
    NotificationCategory,
    NotificationLevel,
    ReminderStage,
    ReminderStatus,
    TaskType,
)
from app.reminder.infrastructure.model import NotificationModel
from app.reminder.infrastructure.repository import NotificationRepository


@pytest.fixture
def db_session():
    """Create in-memory SQLite database session for integration testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    NotificationModel.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_unified_notification_deduplication(db_session):
    repo = NotificationRepository(session=db_session)

    # 1. Ban đầu chưa gửi
    assert (
        repo.has_reminder_been_sent(
            task_type=TaskType.HOMEWORK,
            task_id=1,
            user_id=10,
            stage=ReminderStage.FIXED_0800,
        )
        is False
    )

    # 2. Tạo notification nhắc việc đã gửi
    notif = Notification.create_deadline_reminder(
        user_id=10,
        task_type=TaskType.HOMEWORK,
        task_id=1,
        task_title="Bài tập 1",
        deadline_str="21/10/2026 23:59",
        time_left_str="12 giờ",
        stage=ReminderStage.FIXED_0800,
        action_url="/dashboard/my-homeworks",
        now=datetime.now(),
        discord_status=ReminderStatus.SENT,
    )
    repo.add(notif)

    # 3. Kiểm tra lại đã nhận diện đã gửi
    assert (
        repo.has_reminder_been_sent(
            task_type=TaskType.HOMEWORK,
            task_id=1,
            user_id=10,
            stage=ReminderStage.FIXED_0800,
        )
        is True
    )

    # Khác stage thì chưa gửi
    assert (
        repo.has_reminder_been_sent(
            task_type=TaskType.HOMEWORK,
            task_id=1,
            user_id=10,
            stage=ReminderStage.FIXED_1200,
        )
        is False
    )

    # Kiểm tra get_last_reminder_time
    last_time = repo.get_last_reminder_time(
        task_type=TaskType.HOMEWORK,
        task_id=1,
        user_id=10,
    )
    assert last_time is not None


def test_unified_notification_repository_crud_and_pagination(db_session):
    repo = NotificationRepository(session=db_session)

    # 1. Tạo 3 thông báo cho user 1
    for i in range(1, 4):
        notif = Notification(
            user_id=1,
            title=f"Thông báo {i}",
            content=f"Nội dung {i}",
            category=NotificationCategory.HOMEWORK if i < 3 else NotificationCategory.DUTY,
            level=NotificationLevel.INFO,
            action_url="/dashboard/homeworks",
        )
        repo.add(notif)

    # 2. Đếm chưa đọc
    unread = repo.get_unread_count(user_id=1)
    assert unread == 3

    # 3. Phân trang
    items, total = repo.get_user_notifications(user_id=1, page=1, page_size=2)
    assert total == 3
    assert len(items) == 2

    # Lọc theo category
    duty_items, duty_total = repo.get_user_notifications(
        user_id=1, category=NotificationCategory.DUTY, page=1, page_size=10
    )
    assert duty_total == 1
    assert len(duty_items) == 1

    # 4. Đánh dấu đã đọc 1 thông báo
    first_id = items[0].id
    assert first_id is not None
    marked = repo.mark_as_read(notification_id=first_id, user_id=1)
    assert marked is not None
    assert marked.is_read is True
    assert repo.get_unread_count(user_id=1) == 2

    # 5. Đánh dấu tất cả đã đọc
    marked_count = repo.mark_all_as_read(user_id=1)
    assert marked_count == 2
    assert repo.get_unread_count(user_id=1) == 0
