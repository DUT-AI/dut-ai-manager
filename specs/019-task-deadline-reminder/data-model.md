# Data Model: Automated Task & Deadline Reminder System (Multi-Channel: Discord DM & Web In-App)

**Feature**: `019-task-deadline-reminder`
**Date**: 2026-10-21

## 1. Enums

### `TaskType` (str, Enum)
- `HOMEWORK`: Bài tập về nhà
- `DUTY`: Ca trực nhật vệ sinh
- `MEETING_EVALUATION`: Đánh giá cuộc họp sau 24h

### `ReminderStage` (str, Enum)
- `OFFSET_2D`: 2 ngày trước deadline
- `OFFSET_1D`: 1 ngày trước deadline
- `OFFSET_12H`: 12 giờ trước deadline
- `OFFSET_4H`: 4 giờ trước deadline
- `OFFSET_1H`: 1 giờ trước deadline (khẩn cấp)
- `FIXED_0800`: Quét cố định lúc 08:00 sáng
- `FIXED_1200`: Quét cố định lúc 12:00 trưa
- `FIXED_1930`: Quét cố định lúc 19:30 tối
- `FIXED_2200`: Quét cố định lúc 22:00 tối

### `NotificationCategory` (str, Enum)
- `HOMEWORK`
- `DUTY`
- `MEETING`
- `SYSTEM`

### `NotificationLevel` (str, Enum)
- `INFO`
- `WARNING`
- `CRITICAL`

---

## 2. Domain Entities

### `Notification` (BaseEntity)
```python
class Notification(BaseEntity):
    id: int | None = None
    user_id: int
    title: str
    content: str
    category: NotificationCategory = NotificationCategory.SYSTEM
    level: NotificationLevel = NotificationLevel.INFO
    action_url: str | None = None
    is_read: bool = False
    read_at: datetime | None = None
    
    # Metadata phục vụ Reminder Engine & Deduplication (Chống gửi lặp)
    task_type: TaskType | None = None
    task_id: int | None = None
    reminder_stage: ReminderStage | None = None
    discord_status: str | None = None  # "SENT", "FAILED", "SKIPPED", "NOT_LINKED"
    error_message: str | None = None
    created_at: datetime | None = None
```

---

## 3. Database Schema (PostgreSQL)

### Table: `notifications`
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
    level VARCHAR(50) NOT NULL DEFAULT 'INFO',
    action_url VARCHAR(500),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP WITHOUT TIME ZONE,
    
    -- Metadata Reminder Engine
    task_type VARCHAR(50),
    task_id INTEGER,
    reminder_stage VARCHAR(50),
    discord_status VARCHAR(50),
    error_message TEXT,
    
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index tra cứu danh sách thông báo của user (phân trang & đếm chưa đọc)
CREATE INDEX idx_notif_user_unread ON notifications (user_id, is_read, created_at DESC);

-- Index chống gửi lặp (idempotency): cùng task_type, task_id, user_id, reminder_stage chỉ gửi 1 lần
CREATE INDEX idx_notif_dedup ON notifications (task_type, task_id, user_id, reminder_stage)
WHERE task_type IS NOT NULL AND reminder_stage IS NOT NULL;
```

---

## 4. DTOs

```python
class InAppNotificationDto(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    category: str
    level: str
    action_url: str | None
    is_read: bool
    created_at: datetime

class UnreadCountDto(BaseModel):
    unread_count: int
```
