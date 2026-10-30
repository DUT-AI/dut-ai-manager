"""
NotificationRepository for storing, querying, updating notifications,
and managing reminder deduplication / cooldowns.
"""

from datetime import UTC, datetime

from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.reminder.domain.entity import (
    Notification,
    NotificationCategory,
    PushSubscription,
    ReminderStage,
    TaskType,
)
from app.reminder.domain.repository import PushSubscriptionRepository
from app.reminder.infrastructure.model import (
    NotificationModel,
    PushSubscriptionModel,
)
from app.shared.infrastructure.base_repository import BaseRepository


class NotificationRepository(BaseRepository[NotificationModel, Notification]):
    def __init__(self, session: Session):
        super().__init__(session, NotificationModel)

    # ================= User-facing Feed Methods =================

    def get_user_notifications(
        self,
        user_id: int,
        category: NotificationCategory | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        """Lấy danh sách thông báo phân trang của user có lọc theo category và trạng thái đọc."""
        stmt = select(self.model).where(
            self.model.user_id == user_id,
        )

        if category is not None:
            stmt = stmt.where(self.model.category == category.value)
        if is_read is not None:
            stmt = stmt.where(self.model.is_read == is_read)

        # Tính tổng số bản ghi
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Lấy dữ liệu phân trang
        offset = (page - 1) * page_size
        stmt = (
            stmt.order_by(desc(self.model.created_at)).offset(offset).limit(page_size)
        )
        models = self.session.execute(stmt).scalars().all()

        return [m.to_entity() for m in models], total

    def get_unread_count(self, user_id: int) -> int:
        """Đếm số thông báo chưa đọc của user."""
        stmt = select(func.count(self.model.id)).where(
            self.model.user_id == user_id,
            self.model.is_read.is_(False),
        )
        return self.session.execute(stmt).scalar() or 0

    def mark_as_read(self, notification_id: int, user_id: int) -> Notification | None:
        """Đánh dấu 1 thông báo là đã đọc (bảo vệ quyền sở hữu của user)."""
        now = datetime.now(UTC)
        stmt = (
            update(self.model)
            .where(
                self.model.id == notification_id,
                self.model.user_id == user_id,
            )
            .values(is_read=True, read_at=now)
            .returning(self.model)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            self.session.commit()
            return model.to_entity()
        return None

    def mark_all_as_read(self, user_id: int) -> int:
        """Đánh dấu tất cả thông báo của user là đã đọc."""
        now = datetime.now(UTC)
        stmt = (
            update(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.is_read.is_(False),
            )
            .values(is_read=True, read_at=now)
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount or 0

    # ================= Technical / Reminder Engine Methods =================

    def has_reminder_been_sent(
        self,
        task_type: TaskType,
        task_id: int,
        user_id: int,
        stage: ReminderStage,
    ) -> bool:
        """Kiểm tra xem mốc nhắc nhở cụ thể cho task của user đã từng được gửi chưa."""
        stmt = (
            select(self.model.id)
            .where(
                self.model.task_type == task_type.value,
                self.model.task_id == task_id,
                self.model.user_id == user_id,
                self.model.reminder_stage == stage.value,
            )
            .limit(1)
        )
        result = self.session.execute(stmt).scalar_one_or_none()
        return result is not None

    def get_last_reminder_time(
        self,
        task_type: TaskType,
        task_id: int,
        user_id: int,
    ) -> datetime | None:
        """Lấy thời điểm gửi nhắc nhở gần nhất cho task này của user để áp dụng Cooldown."""
        stmt = (
            select(self.model.created_at)
            .where(
                self.model.task_type == task_type.value,
                self.model.task_id == task_id,
                self.model.user_id == user_id,
            )
            .order_by(desc(self.model.created_at))
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def record_reminder_notification(
        self,
        notification: Notification,
    ) -> Notification:
        """Thêm bản ghi thông báo nhắc nhở vào database."""
        return self.add(notification)


class PushSubscriptionRepositoryImpl(
    BaseRepository[PushSubscriptionModel, PushSubscription],
    PushSubscriptionRepository,
):
    """Hiện thực PushSubscriptionRepository sử dụng SQLAlchemy 2.0 ORM."""

    def __init__(self, session: Session):
        super().__init__(session, PushSubscriptionModel)

    def save_or_update(
        self,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None = None,
    ) -> PushSubscription:
        """Lưu mới hoặc cập nhật thông tin thiết bị đã đăng ký Web Push."""
        stmt = select(self.model).where(self.model.endpoint == endpoint)
        existing = self.session.execute(stmt).scalar_one_or_none()

        now = datetime.now(UTC)
        if existing:
            existing.user_id = user_id
            existing.p256dh = p256dh
            existing.auth = auth
            existing.user_agent = user_agent
            existing.is_active = True
            existing.updated_at = now
            self.session.commit()
            self.session.refresh(existing)
            return existing.to_entity()

        new_sub = PushSubscriptionModel(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_sub)
        self.session.commit()
        self.session.refresh(new_sub)
        return new_sub.to_entity()

    def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        stmt = select(self.model).where(self.model.endpoint == endpoint)
        record = self.session.execute(stmt).scalar_one_or_none()
        return record.to_entity() if record else None

    def get_active_by_user_id(self, user_id: int) -> list[PushSubscription]:
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_active == True,  # noqa: E712
        )
        records = self.session.execute(stmt).scalars().all()
        return [r.to_entity() for r in records]

    def deactivate_endpoint(self, endpoint: str) -> bool:
        stmt = (
            update(self.model)
            .where(self.model.endpoint == endpoint)
            .values(is_active=False, updated_at=datetime.now(UTC))
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def update_last_used(self, subscription_id: int) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id == subscription_id)
            .values(last_used_at=datetime.now(UTC))
        )
        self.session.execute(stmt)
        self.session.commit()

    def delete_endpoint(self, endpoint: str) -> bool:
        stmt = select(self.model).where(self.model.endpoint == endpoint)
        record = self.session.execute(stmt).scalar_one_or_none()
        if record:
            self.session.delete(record)
            self.session.commit()
            return True
        return False
