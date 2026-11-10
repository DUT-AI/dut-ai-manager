# Tasks: Notification Lifecycle, User-driven Delete, and TTL Housekeeping

- **Input**: Design documents from `specs/061-notification-lifecycle-and-cleanup/`
- **Prerequisites**: `spec.md`, `plan.md`, `data-model.md`

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Có thể chạy song song (khác file, độc lập)
- **[Story]**: Gắn với User Story (US1: User Delete 1 Notification, US2: User Delete All Read, US3: TTL Housekeeping Job)

---

## Phase 1: Repository Enhancements (Foundational)

**Mục tiêu**: Bổ sung các phương thức truy vấn và xóa dữ liệu an toàn trong `NotificationRepository`.

- [x] T001 Bổ sung method `delete_by_id_and_user(notification_id: int, user_id: int) -> bool` vào `backend/app/reminder/infrastructure/repository.py` (chỉ xóa khi `id` và `user_id` khớp).
- [x] T002 Bổ sung method `delete_read_by_user(user_id: int) -> int` vào `backend/app/reminder/infrastructure/repository.py` (xóa tất cả bản ghi có `user_id == user_id AND is_read == True`, trả về số lượng row bị xóa).
- [x] T003 Bổ sung method `delete_read_before(cutoff: datetime) -> int` vào `backend/app/reminder/infrastructure/repository.py` (xóa tất cả bản ghi có `is_read == True AND created_at < cutoff`, trả về số lượng row bị xóa).
- [x] T004 [P] Viết unit tests kiểm thử 3 method mới trong `backend/tests/unit/test_notification_repository_cleanup.py`.

---

## Phase 2: User Story 1 & 2 - User-driven Deletion Use Cases & Endpoints (Priority: P1) 🎯 MVP

**Mục tiêu**: Cho phép người dùng xóa 1 thông báo cá nhân hoặc dọn sạch tất cả thông báo đã đọc của mình.

### Implementation Tasks
- [x] T005 [P] [US1] Tạo use case `DeleteNotificationUseCase` trong `backend/app/reminder/application/delete_notification_use_case.py`.
- [x] T006 [P] [US2] Tạo use case `DeleteAllReadNotificationsUseCase` trong `backend/app/reminder/application/delete_all_read_notifications_use_case.py`.
- [x] T007 Đăng ký `DeleteNotificationUseCase` và `DeleteAllReadNotificationsUseCase` vào `ReminderModuleProvider` trong `backend/app/reminder/providers.py`.
- [x] T008 [US1] Thêm endpoint `DELETE /api/v1/notifications/{id}` vào `backend/app/reminder/controller.py`.
- [x] T009 [US2] Thêm endpoint `DELETE /api/v1/notifications/read-all` vào `backend/app/reminder/controller.py`.
- [x] T010 Viết API tests kiểm thử phân quyền và kết quả xóa trong `backend/tests/api/test_notification_deletion_api.py`:
  - User A không thể xóa thông báo của User B (404/403).
  - User A xóa thông báo của chính mình thành công (200).
  - User A gọi `read-all`, chỉ các thông báo `is_read = True` bị xóa, thông báo `is_read = False` vẫn còn nguyên.

---

## Phase 3: User Story 3 - Automated TTL Housekeeping Job (Priority: P2)

**Mục tiêu**: Thiết lập background job tự động dọn dẹp các thông báo đã đọc cũ hơn 30 ngày.

### Implementation Tasks
- [x] T011 [US3] Tạo use case `CleanExpiredNotificationsUseCase` trong `backend/app/reminder/application/clean_expired_notifications_use_case.py` (nhận tham số `retention_days: int = 30`).
- [x] T012 Đăng ký `CleanExpiredNotificationsUseCase` vào `ReminderModuleProvider` trong `backend/app/reminder/providers.py`.
- [x] T013 Tạo scheduler task function `clean_expired_notifications_task` và đăng ký job vào `backend/app/core/scheduler.py` chạy lúc 03:00 sáng hàng ngày.
- [x] T014 Thêm endpoint admin trigger thủ công `POST /api/v1/notifications/housekeeping` trong `backend/app/reminder/controller.py` (để admin hoặc devops có thể kích hoạt dọn dẹp ngay mà không cần chờ đến 03:00 sáng).
- [x] T015 Viết unit test cho `CleanExpiredNotificationsUseCase` trong `backend/tests/unit/test_clean_expired_notifications.py` (kiểm tra không xóa thông báo chưa đọc, chỉ xóa thông báo đã đọc cũ hơn retention period).

---

## Phase 4: Frontend Service Integration (Priority: P3)

**Mục tiêu**: Bổ sung API client methods cho Frontend.

- [x] T016 [P] Bổ sung method `delete(id: number)` và `deleteAllRead()` trong frontend notification service client.

---

## Phase 5: Verification & Regression Testing

**Mục tiêu**: Đảm bảo toàn bộ hệ thống hoạt động ổn định và không làm hồi quy Reminder Engine.

- [x] T017 Chạy toàn bộ test suite: `uv run pytest` đảm bảo tất cả tests mới và 419 tests cũ đều PASSED.
- [x] T018 Chạy `uv run alembic check` xác nhận DB schema hoàn toàn đồng bộ.
