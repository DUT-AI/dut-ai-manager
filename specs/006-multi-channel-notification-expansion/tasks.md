# Tasks: Nâng Cấp Hệ Thống Thông Báo Đa Kênh (Discord & Zalo) & Tích Hợp Assets Meme

**Input**: Design documents from `specs/006-multi-channel-notification-expansion/`
**Prerequisites**: [`plan.md`](./plan.md), [`spec.md`](./spec.md), [`research.md`](./research.md), [`data-model.md`](./data-model.md), [`contracts/notification-service-contract.md`](./contracts/notification-service-contract.md)

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Mapped User Story (US1: Billing/Payment, US2: Homework, US3: Violation & Bonus Point, US4: Meeting & Permission Request)
- File paths are exact and project-relative to repository root.

---

## Phase 1: Setup (Shared Infrastructure & Static Assets)

**Purpose**: Thiết lập endpoint phục vụ hình ảnh tĩnh từ `backend/app/assets` và hạ tầng helper URL.

- [x] T001 [P] Mount thư mục `backend/app/assets` thành static route `/static/assets` bằng `StaticFiles` trong `backend/app/main.py`
- [x] T002 [P] Tạo `asset_helper.py` để sinh URL tuyệt đối cho các tệp meme trong `backend/app/shared/infrastructure/asset_helper.py`

---

## Phase 2: Foundational (Notification Core & Service Dispatcher)

**Purpose**: Xây dựng Value Objects và Unified Notification Service làm nền tảng cho tất cả các domain handler.

- [x] T003 [P] Định nghĩa `NotificationPayload`, `NotificationCategory`, `NotificationLevel` trong `backend/app/shared/infrastructure/notification_payload.py`
- [x] T004 Triển khai `NotificationService` (kết hợp Discord Embed + Zalo Message + Fault Isolation + Exponential Backoff Retry + Fallback an toàn) trong `backend/app/shared/infrastructure/notification_service.py`
- [x] T005 Đăng ký `NotificationService` vào Dishka container trong `backend/app/shared/providers.py`

**Checkpoint**: Nền tảng phân phối thông báo thống nhất đã sẵn sàng cho tất cả các domain use cases.

---

## Phase 3: User Story 1 - Thông Báo Hóa Đơn & Thanh Toán Thành Công (Priority: P1) 🎯 MVP

**Goal**: Gửi thông báo phát hành hóa đơn mới (kèm meme xin tiền) và thông báo thanh toán thành công qua SePay webhook (kèm meme chúc mừng).

**Independent Test**: Tạo hóa đơn mới cho người dùng và giả lập webhook SePay thanh toán thành công, xác minh Discord và Zalo đều nhận được tin nhắn kèm meme tương ứng.

- [x] T006 [P] [US1] Định nghĩa Domain Events `InvoiceCreated` và `InvoicePaid` trong `backend/app/billing/domain/events.py`
- [x] T007 [US1] Cập nhật `CreateInvoiceUseCase` và `CreateMonthlyInvoicesUseCase` để phát sự kiện `InvoiceCreated` trong `backend/app/billing/application/use_cases.py`
- [x] T008 [US1] Cập nhật `HandleSePayWebhookUseCase` để phát sự kiện `InvoicePaid` khi giao dịch hợp lệ trong `backend/app/billing/application/use_cases.py`
- [x] T009 [US1] Tạo `BillingNotificationHandler` xử lý `InvoiceCreated` (`meme-xin-tien.jpeg`) và `InvoicePaid` (`meme-lam-viec-3.jpeg`) trong `backend/app/billing/application/notification_handler.py`
- [x] T010 [US1] Đăng ký `BillingNotificationHandler` vào `backend/app/billing/providers.py` và liên kết sự kiện trong `backend/app/core/events.py`

**Checkpoint**: User Story 1 hoàn thành độc lập và có thể kiểm thử luồng thanh toán / hóa đơn từ A-Z.

---

## Phase 4: User Story 2 - Nâng Cấp Thông Báo Bài Tập (Homework) (Priority: P1)

**Goal**: Nâng cấp thông báo giao bài tập và chấm điểm bài tập sử dụng `NotificationService` và đính kèm meme học bài.

**Independent Test**: Giao bài tập mới và chấm điểm bài tập của học viên, xác minh tin nhắn Discord (Embed xanh) và Zalo hiển thị kèm `meme-hoc-bai.webp` / `meme-lam-viec-2.jpeg`.

- [x] T011 [US2] Refactor `HomeworkNotificationHandler` để sử dụng `NotificationService` kèm `meme-hoc-bai.webp` trong `backend/app/homework/application/event_handlers.py`
- [x] T012 [US2] Refactor `HomeworkGradedNotificationHandler` để sử dụng `NotificationService` kèm `meme-lam-viec-2.jpeg` trong `backend/app/homework/application/event_handlers.py`

**Checkpoint**: User Story 2 hoàn thành độc lập và kiểm thử gửi thông báo bài tập thành công.

---

## Phase 5: User Story 3 - Nâng Cấp Thông Báo Vi Phạm & Điểm Thưởng (Violation & Bonus Point) (Priority: P1)

**Goal**: Nâng cấp thông báo biên bản vi phạm và cộng/trừ điểm thưởng sử dụng meme đòi nợ / khóc / ngạc nhiên.

**Independent Test**: Ghi nhận 1 vi phạm mới và tạo 1 giao dịch cộng điểm thưởng, xác minh Discord và Zalo nhận thông báo kèm `meme-doi-no-2.jpg` và `meme-ngac-nhien.jpeg`.

- [x] T013 [P] [US3] Refactor `ViolationNotificationHandler` sử dụng `NotificationService` kèm `meme-doi-no-2.jpg` và `meme-khoc.webp` trong `backend/app/violation/notification_handler.py`
- [x] T014 [P] [US3] Refactor `BonusPointNotificationHandler` sử dụng `NotificationService` kèm `meme-xin-tien.jpeg` và `meme-ngac-nhien.jpeg` trong `backend/app/bonus_point/notification_handler.py`

**Checkpoint**: User Story 3 hoàn thành độc lập và kiểm thử thông báo vi phạm/điểm thưởng trơn tru.

---

## Phase 6: User Story 4 - Nâng Cấp Thông Báo Buổi Sinh Hoạt & Đơn Xin Phép (Meeting & Permission Request) (Priority: P1)

**Goal**: Nâng cấp thông báo lịch học, điểm danh và đơn xin phép sử dụng `NotificationService` và meme nhắc nhở.

**Independent Test**: Tạo buổi học mới, check-in thành công và nộp đơn xin phép, xác minh thông báo gửi đến người tham gia và Discord room quản trị kèm `anh-nhac-em-meme-9.webp`.

- [x] T015 [P] [US4] Refactor `MeetingNotificationHandler` sử dụng `NotificationService` kèm `anh-nhac-em-meme-9.webp` và `meme-lam-viec.webp` trong `backend/app/meeting/application/event_handlers.py`
- [x] T016 [P] [US4] Refactor `PermissionRequestNotificationHandler` sử dụng `NotificationService` kèm `anh-nhac-em-meme-9.webp` trong `backend/app/permission_request/application/event_handlers.py`

**Checkpoint**: Toàn bộ 6 use case trong hệ thống đã được đồng bộ hóa và nâng cấp hoàn chỉnh.

---

## Phase 7: Polish & Validation

**Purpose**: Kiểm thử tự động tổng thể, bảo đảm không có regression và kiểm tra toàn vẹn tài nguyên.

- [x] T017 [P] Viết unit test cho `NotificationService` (kiểm tra fault isolation, retry logic, image fallback) trong `backend/tests/unit/test_notification_service.py`
- [x] T018 [P] Viết integration test cho `BillingNotificationHandler` trong `backend/tests/unit/test_billing_notifications.py`
- [x] T019 Chạy toàn bộ test suite và thực hiện kịch bản nghiệm thu theo `specs/006-multi-channel-notification-expansion/quickstart.md`

---

## Dependencies & Execution Order

1. **Phase 1 (Setup)** & **Phase 2 (Foundational)**: Bắt buộc thực hiện trước tiên để tạo `NotificationService` và static mount.
2. **Phase 3 (User Story 1 - Billing & Payment - MVP)**: Triển khai trước tiên để kiểm chứng luồng Event-Driven + Meme đầy đủ.
3. **Phase 4 (US2)**, **Phase 5 (US3)**, **Phase 6 (US4)**: Có thể thực thi song song sau khi Phase 2 và Phase 3 hoàn thành.
4. **Phase 7 (Polish)**: Thực hiện cuối cùng để xác nhận toàn bộ test cases pass 100%.

---

## Parallel Opportunities

- **T001 & T002**: Setup static mount và asset helper chạy độc lập song song.
- **T013 & T014**: Nâng cấp Violation và Bonus Point có thể thực hiện song song.
- **T015 & T016**: Nâng cấp Meeting và Permission Request có thể thực hiện song song.
- **T017 & T018**: Viết test cases cho Notification Service và Billing Handler song song.
