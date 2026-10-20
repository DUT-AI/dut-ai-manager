# Implementation Plan: Automated Task & Deadline Reminder System (Multi-Channel: Discord DM & Web Notifications Tab)

**Branch**: `019-task-deadline-reminder` | **Date**: 2026-10-21 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/019-task-deadline-reminder/spec.md)

## Summary
Triển khai hệ thống nhắc nhở công việc và nhiệm vụ trước hạn đa kênh:
- **Discord Bot**: Bắn tin nhắn riêng (DM) trực tiếp tới Discord thành viên.
- **Web App (Tab Quản lý Thông báo)**: Thêm 1 trang/tab riêng biệt trên thanh Sidebar Menu (`/dashboard/notifications`) với icon Chuông (`BellOutlined`), cho phép thành viên lọc, xem danh sách thông báo nhắc vi## Technical Context
- **Language/Version**: Python 3.12 (Backend) + TypeScript / React 18 (Frontend)
- **Primary Dependencies**: FastAPI, Dishka (DI), SQLAlchemy 2.0, APScheduler, Ant Design v5 (Frontend UI)
- **Storage**: PostgreSQL (`notifications`) - Gộp thành 1 bảng duy nhất lưu trữ cả thông báo hiển thị cho User và metadata chống gửi lặp (idempotency) + cooldown 3h.
- **Testing**: pytest (Backend) + Vite build check (Frontend)
- **Target Platform**: Linux Server / Docker Compose (Web & API)
- **Timezone**: Asia/Ho_Chi_Minh (UTC+7) cho mọi tính toán thời gian và so sánh hạn chót.

## Constitution Check
- **Principle I (Clean Architecture & Practical DDD Boundaries)**: PASS. Tạo domain model `Notification` chứa đầy đủ logic nghiệp vụ tính mốc nhắc nhở (`calculate_matching_stages`), độ khẩn cấp (`is_critical`), cooldown 3h (`is_within_cooldown`). Repository `NotificationRepository` truy vấn dữ liệu độc lập.
- **Principle II (Dependency Injection with Dishka)**: PASS. Toàn bộ use cases, scanners, dispatcher và repositories được inject qua Dishka container trong `ReminderModuleProvider`.
- **Principle VII (Strict Single-Responsibility Use Cases & Scanners)**: PASS.
  - Tách các Task Scanners theo Strategy Pattern: `HomeworkTaskScanner`, `DutyTaskScanner`, `MeetingEvaluationTaskScanner`.
  - `ReminderDispatcher`: Chuyên biệt hóa việc dispatch thông báo đa kênh (Discord DM + Database Notification).
  - `scan_and_send_reminders_use_case.py`: Đóng vai trò Orchestrator cực gọn điều phối scanners, kiểm tra chống trùng lặp và chuyển cho dispatcher.
  - `get_my_notifications_use_case.py`: Lấy danh sách thông báo phân trang của user.
  - `get_unread_notification_count_use_case.py`: Đếm số lượng thông báo chưa đọc.
  - `mark_notification_as_read_use_case.py`: Đánh dấu 1 thông báo đã đọc.
  - `mark_all_notifications_as_read_use_case.py`: Đánh dấu tất cả thông báo đã đọc.
  - *(Đã lược bỏ DeleteNotificationUseCase do đã bỏ tính năng xóa thông báo).*
- **Principle VIII (Frontend Component Modularity & Single-Responsibility UI)**: PASS. 
  - Màn hình `NotificationManagementPage.tsx` đóng vai trò Orchestrator.
  - Subcomponents đặt riêng trong `features/notification/components/`: `NotificationFilter.tsx`, `NotificationTable.tsx`, `NotificationDetailModal.tsx`.
  - Bảng dữ liệu có phân trang chuẩn (`defaultPageSize >= 20`, `pageSizeOptions: ['10', '20', '50', '100']`).
  - Lược bỏ nút xóa trên UI để tối ưu hóa trải nghiệm vào trạng thái Đã đọc / Chưa đọc.
- **Principle X (Zero Redundant Backward Compatibility)**: PASS. Không tạo alias hay duplicate API.

## Project Structure

### Documentation (this feature)
```text
specs/019-task-deadline-reminder/
├── spec.md              # Đặc tả yêu cầu người dùng
├── checklists/          # Checklist kiểm định chất lượng
│   └── requirements.md
├── plan.md              # Kế hoạch kiến trúc (File hiện tại)
├── research.md          # Phân tích kỹ thuật & ra quyết định
├── data-model.md        # Thiết kế Entity & Database Schema
├── contracts/           # API Contracts & JSON Schemas
│   └── trigger-reminder-response.json
├── quickstart.md        # Hướng dẫn kiểm thử & chạy xác thực
└── tasks.md             # Danh sách phân rã tasks thực thi
```

### Source Code

#### Backend
```text
backend/
├── alembic/versions/
│   └── xxxx_create_unified_notifications_table.py
├── app/
│   ├── reminder/
│   │   ├── domain/
│   │   │   └── entity.py                # Notification, ReminderStage, TaskType, NotificationCategory
│   │   ├── application/
│   │   │   ├── dtos.py
│   │   │   ├── scanners/
│   │   │   │   ├── base_scanner.py
│   │   │   │   ├── homework_scanner.py
│   │   │   │   ├── duty_scanner.py
│   │   │   │   └── meeting_evaluation_scanner.py
│   │   │   ├── reminder_dispatcher.py
│   │   │   ├── scan_and_send_reminders_use_case.py
│   │   │   ├── get_my_notifications_use_case.py
│   │   │   ├── get_unread_notification_count_use_case.py
│   │   │   ├── mark_notification_as_read_use_case.py
│   │   │   └── mark_all_notifications_as_read_use_case.py
│   │   ├── infrastructure/
│   │   │   ├── model.py                 # NotificationModel (Unified table 'notifications')
│   │   │   └── repository.py            # NotificationRepository (xử lý cả query UI & dedup log)
│   │   ├── controller.py                # REST Endpoints: /notifications & /reminders
│   │   └── providers.py                 # Dishka ReminderModuleProvider
│   ├── jobs/
│   │   └── reminder_scanner_job.py
│   └── core/
│       └── scheduler.py
```

#### Frontend
```text
frontend/
├── src/
│   ├── config/
│   │   └── menu.tsx                     # Bổ sung tab 'Thông báo' vào sidebarMenuConfig
│   ├── routes/
│   │   └── dashboardRoutes.tsx          # Bổ sung route '/dashboard/notifications'
│   └── features/
│       └── notification/
│           ├── types/
│           │   └── notification.types.ts
│           ├── services/
│           │   └── notification.service.ts
│           ├── hooks/
│           │   └── useInAppNotifications.ts
│           ├── components/
│           │   ├── NotificationFilter.tsx
│           │   ├── NotificationTable.tsx
│           │   ├── NotificationDetailModal.tsx
│           │   └── index.ts
│           ├── pages/
│           │   ├── NotificationManagementPage.tsx
│           │   └── index.ts
│           └── index.ts
```

## Implementation Phases

### Phase 1: Kiến trúc dữ liệu thống nhất (Unified Database & Domain)
1. Cập nhật `Notification` Entity: tích hợp các trường kỹ thuật (`task_type`, `task_id`, `reminder_stage`, `discord_status`, `error_message`). Đóng gói logic tính stage, cooldown và is_critical ngay trong domain.
2. Cập nhật `NotificationModel` ánh xạ vào bảng `notifications`.
3. Tạo Alembic migration chuyển đổi/khởi tạo bảng `notifications` duy nhất.
4. Triển khai `NotificationRepository`: tích hợp cả các phương thức hiển thị (`get_user_notifications`, `mark_as_read`, `get_unread_count`) và các phương thức chống trùng lặp (`has_reminder_been_sent`, `get_last_reminder_time`).

### Phase 2: Refactor Use Cases & Scanners
1. Hoàn thiện 3 Scanners chuyên trách:
   - `HomeworkTaskScanner`: Quét bài tập còn hạn.
   - `DutyTaskScanner`: Quét ca trực vệ sinh hôm nay.
   - `MeetingEvaluationTaskScanner`: Quét đánh giá cuộc họp 2 chiều (inject `MeetingEvaluationRepository`).
2. Cập nhật `ReminderDispatcher`: Gửi Discord DM kèm embed + lưu bản ghi vào `NotificationRepository`.
3. Cập nhật `ScanAndSendRemindersUseCase`: Orchestrator điều phối các scanner và kiểm tra `has_reminder_been_sent`.
4. Xóa bỏ `DeleteNotificationUseCase` và endpoint `DELETE /api/v1/notifications/{id}`.

### Phase 3: Tinh gọn Frontend UI
1. Xóa bỏ hàm `deleteNotificationApi` và mutation delete trong `useInAppNotifications.ts`.
2. Lược bỏ nút xóa (icon thùng rác) khỏi `NotificationTable.tsx`.
3. Giữ nguyên toàn bộ tính năng lọc, phân trang, đánh dấu đã đọc, đánh dấu tất cả đã đọc và điều hướng nộp bài.

### Phase 4: Kiểm thử & Xác nhận chất lượng
1. Chạy toàn bộ Unit Tests trong `tests/unit/test_reminder_use_cases.py`.
2. Chạy API Tests trong `tests/api/test_notification_api.py`.
3. Chạy Integration Tests trong `tests/integration/test_reminder_integration.py`.
4. Chạy `npm run build` trên frontend đảm bảo không lỗi kiểu hoặc import thừa.
5. Kiểm tra toàn bộ pytest suite dự án đảm bảo không gây regression.
