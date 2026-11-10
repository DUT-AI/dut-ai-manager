# Implementation Plan: Notification Lifecycle, User-driven Delete, and TTL Housekeeping

- **Feature**: `specs/061-notification-lifecycle-and-cleanup`
- **Spec**: `specs/061-notification-lifecycle-and-cleanup/spec.md`
- **Status**: Ready for Tasks

---

## 1. Technical Context & Scope

### 1.1 Architecture & Components
- **Repository Layer**:
  - `NotificationRepository` kế thừa `BaseRepository[NotificationModel, Notification]`.
  - Cần thêm:
    1. `delete_by_id_and_user(notification_id: int, user_id: int) -> bool`: Xóa 1 thông báo thuộc sở hữu của user (hard delete).
    2. `delete_read_by_user(user_id: int) -> int`: Xóa tất cả thông báo `is_read = true` của user.
    3. `delete_read_before(cutoff: datetime) -> int`: Xóa tất cả thông báo `is_read = true` có `created_at < cutoff` (phục vụ TTL housekeeping).
- **Application Layer (Use Cases)**:
  - `DeleteNotificationUseCase`: Thực thi xóa 1 notification nếu thuộc về `current_user.id`.
  - `DeleteAllReadNotificationsUseCase`: Thực thi xóa tất cả notification đã đọc của `current_user.id`.
  - `CleanExpiredNotificationsUseCase`: Thực thi quét và dọn các bản ghi notification đã đọc > 30 ngày (mặc định).
- **Presentation / API Layer**:
  - `DELETE /api/v1/notifications/{id}` -> `DeleteNotificationUseCase`.
  - `DELETE /api/v1/notifications/read-all` -> `DeleteAllReadNotificationsUseCase`.
- **Background Scheduler Integration**:
  - Đăng ký job `clean_expired_notifications_job` vào `app/core/scheduler.py` chạy lúc 03:00 sáng hàng ngày (hoặc hàng tuần).
- **DI Container (Dishka)**:
  - Đăng ký 3 use case mới vào `ReminderModuleProvider` ([backend/app/reminder/providers.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/reminder/providers.py)).
- **Frontend Layer**:
  - Bổ sung `delete(id)` và `deleteAllRead()` trong `frontend/src/features/reminder/services/notification.service.ts` (hoặc tương ứng).

---

## 2. Risk & Constitution Check

1. **Risk 1: Vô tình xóa thông báo của người khác**:
   - *Mitigation*: Mọi query xóa theo user bắt buộc có mệnh đề `WHERE user_id = :current_user_id`. Nếu ID không khớp hoặc không tồn tại, trả về `404 Not Found`.
2. **Risk 2: Xóa nhầm thông báo chưa đọc trong Housekeeping**:
   - *Mitigation*: Housekeeping query bắt buộc có `WHERE is_read = True AND created_at < :cutoff`. Không bao giờ xóa thông báo chưa đọc.
3. **Risk 3: Xung đột với Reminder Deduplication**:
   - *Mitigation*: Reminder engine kiểm tra các task diễn ra trong tương lai hoặc gần đây (ví dụ deadline trong 24h, meeting sắp tới trong 2h). Housekeeping chỉ xóa thông báo cũ hơn **30 ngày**, khi các task đó đã hoàn tất/kết thúc từ lâu. Không có nguy cơ tái kích hoạt reminder cũ.

---

## 3. Phased Implementation Roadmap

- **Phase 1: Repository Enhancements**
  - Viết các method xóa trong `NotificationRepository`.
  - Viết unit test cho repository methods.
- **Phase 2: Use Cases & Providers**
  - Implement `DeleteNotificationUseCase`, `DeleteAllReadNotificationsUseCase`, `CleanExpiredNotificationsUseCase`.
  - Đăng ký provider vào Dishka container.
  - Viết unit tests cho use cases.
- **Phase 3: Controller Endpoints & API Tests**
  - Thêm router `DELETE /{id}` và `DELETE /read-all` trong `backend/app/reminder/controller.py`.
  - Viết API integration tests kiểm tra ownership, response status, và đếm số lượng bản ghi đã xóa.
- **Phase 4: Scheduler Housekeeping Job**
  - Đăng ký job trong `app/core/scheduler.py`.
  - Viết unit test cho scheduler execution.
- **Phase 5: Frontend Integration**
  - Bổ sung client calls trong frontend service và UI.
- **Phase 6: Full Verification**
  - Chạy `uv run pytest` và `uv run alembic check`.
