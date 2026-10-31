# Phase 1: Data Model & Schema Changes (039-per-assignee-homework-deadline)

## 1. Database Schema Changes

### Bảng `homeworks`
Xóa cột `deadline`.
```sql
ALTER TABLE homeworks DROP COLUMN deadline;
```

### Bảng `homework_assignees`
Bổ sung cột `deadline TIMESTAMPTZ NOT NULL` có index.
```sql
-- 1. Thêm cột tạm thời cho phép NULL
ALTER TABLE homework_assignees 
ADD COLUMN deadline TIMESTAMPTZ NULL;

-- 2. Backfill deadline từ homeworks
UPDATE homework_assignees ha
SET deadline = h.deadline
FROM homeworks h
WHERE ha.homework_id = h.id AND ha.deadline IS NULL;

-- 3. Cập nhật deadline cho các đơn xin hoãn POSTPONE đang có hiệu lực
UPDATE homework_assignees ha
SET deadline = pr.start_time
FROM permission_requests pr
WHERE pr.category = 'POSTPONE'
  AND (pr.payload->>'homework_id')::int = ha.homework_id
  AND pr.user_id = ha.user_id
  AND pr.is_deleted = false
  AND pr.start_time IS NOT NULL;

-- 4. Đặt NOT NULL và đánh chỉ mục
ALTER TABLE homework_assignees 
ALTER COLUMN deadline SET NOT NULL;

CREATE INDEX ix_homework_assignees_deadline ON homework_assignees (deadline);

-- 5. Xoá cột deadline ở bảng homeworks
ALTER TABLE homeworks DROP COLUMN deadline;
```

---

## 2. SQLAlchemy ORM Models

### `HomeworkModel` (`backend/app/homework/infrastructure/model.py`)
```python
class HomeworkModel(SQLAlchemyTimestampMixin, Base):
    """Homework model containing assignment details (Không còn cột deadline)"""

    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    link: Mapped[str | None] = mapped_column(String(500), default=None, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True)
    requires_coding: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    requires_game: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    assignees: Mapped[list["HomeworkAssigneeModel"]] = relationship(
        back_populates="homework", cascade="all, delete-orphan", lazy="selectin"
    )
    submissions: Mapped[list["HomeworkSubmissionModel"]] = relationship(
        back_populates="homework", cascade="all, delete-orphan", lazy="selectin"
    )
```

### `HomeworkAssigneeModel` (`backend/app/homework/infrastructure/model.py`)
```python
class HomeworkAssigneeModel(SQLAlchemyTimestampMixin, Base):
    """Mapping between Homework and direct User assignees with individual deadline"""

    __tablename__ = "homework_assignees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    homework: Mapped[HomeworkModel] = relationship(back_populates="assignees")
```

---

## 3. Domain Entities & Value Objects

### `Homework` Entity (`backend/app/homework/domain/entity.py`)
```python
@dataclass
class Homework(BaseEntity):
    title: str
    link: str | None = None
    slug: str | None = None
    requires_coding: bool = True
    requires_game: bool = False
    # Đã xoá deadline ở cấp Homework entity
```

### `HomeworkAssignee` Entity (`backend/app/homework/domain/entity.py`)
```python
@dataclass
class HomeworkAssignee(BaseEntity):
    homework_id: int
    user_id: int
    deadline: datetime
```

### `PostponePayload` (`backend/app/permission_request/domain/payloads.py`)
```python
class PostponePayload(BasePermissionPayload):
    """Payload cho đơn xin hoãn nộp bài tập (POSTPONE)."""

    category: Literal[RequestCategory.POSTPONE] = RequestCategory.POSTPONE
    homework_id: int | None = None
    start_time: datetime | None = None  # Mốc deadline mới xin gia hạn
    old_deadline: datetime | None = None  # Mốc deadline cũ trước khi xin hoãn (dùng để hoàn nguyên khi xoá đơn)
```

### `DueHomeworkAssignment` (`backend/app/homework/domain/value_objects.py`)
```python
@dataclass(frozen=True)
class DueHomeworkAssignment:
    homework_id: int
    user_id: int
    homework_title: str
    deadline: datetime  # Deadline cá nhân của học viên
    requires_coding: bool
    requires_game: bool
```
