# Tasks: Automated Task & Deadline Reminder System (Multi-Channel: Discord DM & Web Notifications Tab)

**Input**: Design documents from `specs/019-task-deadline-reminder/`
- Spec: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/019-task-deadline-reminder/spec.md)
- Plan: [plan.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/019-task-deadline-reminder/plan.md)
- Data Model: [data-model.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/019-task-deadline-reminder/data-model.md)

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Có thể chạy song song (khác tệp, không phụ thuộc vào task chưa hoàn thành)
- **[Story]**: Gắn nhãn User Story tương ứng (`[US1]`, `[US2]`, `[US3]`, `[US4]`)

---

## Phase 1: Setup & Foundational Infrastructure (Backend Tables & Repositories)

- [X] T001 Tạo cấu trúc thư mục module `backend/app/reminder/` (`domain/`, `application/`, `infrastructure/`)
- [X] T002 [P] Định nghĩa Enums `TaskType`, `ReminderStage`, `NotificationCategory`, `NotificationLevel` trong `backend/app/reminder/domain/entity.py`
- [X] T003 [P] Định nghĩa Domain Entity `Notification` (gộp chung cả dữ liệu hiển thị lẫn metadata kỹ thuật) trong `backend/app/reminder/domain/entity.py`
- [X] T004 [P] Định nghĩa DTOs cho Notifications & Reminders trong `backend/app/reminder/application/dtos.py`
- [X] T005 [P] Cập nhật SQLAlchemy ORM Model `NotificationModel` (bảng `notifications`) trong `backend/app/reminder/infrastructure/model.py`
- [X] T006 [P] Cập nhật `NotificationRepository` (tích hợp query UI, đánh dấu đã đọc và kiểm tra deduplication/cooldown) trong `backend/app/reminder/infrastructure/repository.py`
- [X] T007 Tạo migration Alembic chuyển đổi sang bảng `notifications` thống nhất trong `backend/alembic/versions/`

**Checkpoint**: Nền tảng database và repository thống nhất sẵn sàng.

---

## Phase 2: User Story 2 - Trang Quản lý Thông báo trên Web Sidebar (`/dashboard/notifications`) (Priority: P1) 🎯 Core Web Feature

### Backend Use Cases & API for In-App Notifications
- [X] T008 [P] [US2] Xây dựng `GetMyNotificationsUseCase` trong `backend/app/reminder/application/get_my_notifications_use_case.py`
- [X] T009 [P] [US2] Xây dựng `GetUnreadNotificationCountUseCase` trong `backend/app/reminder/application/get_unread_notification_count_use_case.py`
- [X] T010 [P] [US2] Xây dựng `MarkNotificationAsReadUseCase` trong `backend/app/reminder/application/mark_notification_as_read_use_case.py`
- [X] T011 [P] [US2] Xây dựng `MarkAllNotificationsAsReadUseCase` trong `backend/app/reminder/application/mark_all_notifications_as_read_use_case.py`
- [X] T012 [P] [US2] Xóa bỏ `DeleteNotificationUseCase` và endpoint `DELETE /api/v1/notifications/{id}` khỏi `backend/app/reminder/controller.py`

### Frontend Web UI: Tinh gọn Giao diện Thông báo
- [X] T013 [P] [US2] TypeScript types cho thông báo trong `frontend/src/features/notification/types/notification.types.ts`
- [X] T014 [P] [US2] Bỏ `deleteNotificationApi` trong `frontend/src/features/notification/services/notification.service.ts`
- [X] T015 [P] [US2] Bỏ mutation delete khỏi `frontend/src/features/notification/hooks/useInAppNotifications.ts`
- [X] T016 [P] [US2] Subcomponent `NotificationFilter.tsx` lọc theo danh mục và trạng thái đọc
- [X] T017 [P] [US2] Bỏ nút xóa (icon thùng rác) khỏi `frontend/src/features/notification/components/NotificationTable.tsx`
- [X] T018 [P] [US2] Subcomponent `NotificationDetailModal.tsx`
- [X] T019 [US2] Trang Orchestrator `NotificationManagementPage.tsx`
- [X] T020 [US2] Thêm route `/dashboard/notifications` trong `frontend/src/routes/dashboardRoutes.tsx`
- [X] T021 [US2] Thêm mục menu **"Thông báo"** với icon `BellOutlined` vào Sidebar Menu trong `frontend/src/config/menu.tsx`

---

## Phase 3: User Story 1 - Discord DM Bot, Task Scanners & Dispatcher (Priority: P1)

- [X] T022 [P] [US1] Xây dựng `embed_builder.py` tạo Discord Rich Embed cảnh báo chi tiết
- [X] T023 [P] [US1] Tách các Task Scanners: `HomeworkTaskScanner`, `DutyTaskScanner`, `MeetingEvaluationTaskScanner` theo Strategy Pattern
- [X] T024 [US1] Cập nhật `ReminderDispatcher` ghi trực tiếp bản ghi vào `NotificationRepository`
- [X] T025 [US1] Cập nhật `ScanAndSendRemindersUseCase` kiểm tra deduplication trực tiếp từ `NotificationRepository`
- [X] T026 [US1] Cập nhật Dishka Provider `ReminderModuleProvider` trong `backend/app/reminder/providers.py`
- [X] T027 [P] [US1] Cập nhật unit tests cho `NotificationRepository` và `ScanAndSendRemindersUseCase` trong `backend/tests/unit/test_reminder_use_cases.py`

---

## Phase 4: User Story 3 & 4 - Hybrid Scheduler, Chống lặp & Admin Trigger (Priority: P2 & P3)

- [X] T028 [US3] Thuật toán nhận diện mốc `ReminderStage` Hybrid và cooldown 3h
- [X] T029 [US3] Worker job `reminder_scanner_job.py` trong `backend/app/jobs/`
- [X] T030 [US3] Đăng ký job quét định kỳ vào `APScheduler` trong `backend/app/core/scheduler.py`
- [X] T031 [US4] Endpoint kích hoạt quét thủ công `/api/v1/reminders/trigger` cho Admin
- [X] T032 [P] [US3] Cập nhật integration tests và API tests trong `backend/tests/`

---

## Phase 5: Hoàn thiện, Kiểm thử & Build Check

- [X] T033 Dọn dẹp re-export trong `backend/app/reminder/__init__.py` và `backend/app/reminder/infrastructure/__init__.py`
- [X] T034 Chạy `npm run build` trên frontend để xác thực không có lỗi TypeScript
- [X] T035 Chạy toàn bộ test suite backend `pytest backend/tests/` đảm bảo 100% passed không phát sinh regression
