# Data Model & Contracts: Notification Lifecycle & Cleanup

- **Feature**: `specs/061-notification-lifecycle-and-cleanup`

## 1. Data Model (SQLAlchemy & Database)

Không có thay đổi về Schema DDL trong Database vì bảng `notifications` đã là Hard Delete (`SQLAlchemyAuditTimestampMixin` - không có `is_deleted`).

```sql
-- Cấu trúc bảng notifications hiện tại (PostgreSQL)
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
    level VARCHAR(20) NOT NULL DEFAULT 'INFO',
    action_url VARCHAR(500),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Technical / Reminder Engine fields
    task_type VARCHAR(50),
    task_id INTEGER,
    reminder_stage VARCHAR(50),
    discord_status VARCHAR(20),
    zalo_status VARCHAR(20),
    web_push_status VARCHAR(20),
    error_message TEXT,
    metadata_json JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);
CREATE INDEX ix_notifications_is_read ON notifications (is_read);
CREATE INDEX ix_notifications_created_at ON notifications (created_at);
```

## 2. API Contracts

### 2.1 Xóa một thông báo cá nhân
- **Endpoint**: `DELETE /api/v1/notifications/{id}`
- **Auth**: Bearer Token
- **Path Parameter**: `id: int`
- **Response**:
  - `200 OK`:
    ```json
    {
      "is_success": true,
      "data": true,
      "message": "Xóa thông báo thành công"
    }
    ```
  - `404 Not Found`:
    ```json
    {
      "is_success": false,
      "message": "Không tìm thấy thông báo hoặc bạn không có quyền xóa"
    }
    ```

### 2.2 Xóa tất cả thông báo đã đọc của cá nhân
- **Endpoint**: `DELETE /api/v1/notifications/read-all`
- **Auth**: Bearer Token
- **Response**:
  - `200 OK`:
    ```json
    {
      "is_success": true,
      "data": 15,
      "message": "Đã xóa 15 thông báo đã đọc"
    }
    ```

### 2.3 Quét dọn tự động định kỳ (Admin / Cron / Trigger)
- **Use Case**: `CleanExpiredNotificationsUseCase`
- **Method**: `execute(retention_days: int = 30) -> int`
- **SQL Logic**:
  ```sql
  DELETE FROM notifications
  WHERE is_read = TRUE 
    AND created_at < NOW() - INTERVAL '30 days';
  ```
