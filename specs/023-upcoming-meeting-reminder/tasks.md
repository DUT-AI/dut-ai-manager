# Tasks: Nhắc Nhở Buổi Họp / Lịch Sinh Hoạt Sắp Diễn Ra Cho Thành Viên (Upcoming Meeting Attendance Reminder)

**Input**: Design documents from `specs/023-upcoming-meeting-reminder/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no blocking dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Kiểm tra cấu hình và môi trường trước khi triển khai tính năng

- [X] T001 [P] Verify project dependencies and environment for Reminder module in `backend/app/reminder/`
- [X] T002 [P] Confirm Meeting domain models and repository query contracts in `backend/app/meeting/domain/entity.py` and `backend/app/meeting/infrastructure/repository.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Mở rộng các Domain Entity và Embed Builder dùng chung trước khi triển khai các User Story

⚠️ **CRITICAL**: Hoàn thành pha này trước khi triển khai các User Story

- [X] T003 [P] Add `MEETING = "MEETING"` to `TaskType` enum in `backend/app/reminder/domain/entity.py`
- [X] T004 [P] Update `Notification.create_deadline_reminder` factory in `backend/app/reminder/domain/entity.py` to map `TaskType.MEETING` to `NotificationCategory.MEETING` with custom title (`Nhắc nhở cuộc họp sắp diễn ra: {task_title}`) and meeting-specific content
- [X] T005 [P] Update `build_reminder_embed` in `backend/app/reminder/application/embed_builder.py` to format `TaskType.MEETING` with title `⏰ [NHẮC NHỞ LỊCH HỌP] Buổi họp / Sinh hoạt: {task_title}` and action link leading to `/dashboard/meetings/{meeting_id}`

**Checkpoint**: Nền tảng Domain và Formatters đã sẵn sàng để phát triển các Story độc lập.

---

## Phase 3: User Story 1 - Thành viên nhận thông báo nhắc nhở chuẩn bị tham gia buổi họp sắp diễn ra (Priority: P1) 🎯 MVP

**Goal**: Thành viên được phân công tham gia nhận thông báo nhắc nhở trước khi buổi họp bắt đầu qua đa kênh (Web In-App, Discord DM, PWA Web Push) kèm liên kết trực tiếp mở trang chi tiết buổi họp.

**Independent Test**: Tạo một buổi họp diễn ra sau 1 giờ với thành viên ở trạng thái `NOT_JOINED`, kích hoạt scanner $\rightarrow$ phát hiện ứng viên với mốc `OFFSET_1H`, đếm ngược 1 giờ và liên kết `/dashboard/meetings/{id}`.

### Tests for User Story 1

- [X] T006 [P] [US1] Create unit test suite `test_upcoming_meeting_scanner.py` in `backend/tests/unit/test_upcoming_meeting_scanner.py` covering candidate scanning, 48h lookahead window, and stage calculation

### Implementation for User Story 1

- [X] T007 [US1] Implement `UpcomingMeetingTaskScanner` in `backend/app/reminder/application/scanners/upcoming_meeting_scanner.py` inheriting `BaseTaskScanner` with 48h lookahead window and `calculate_matching_stages`
- [X] T008 [US1] Filter out members who already checked in (`p.status in (ParticipantStatus.JOINED, ParticipantStatus.COMPLETED)`) or are soft-deleted (`p.is_deleted == True`) in `backend/app/reminder/application/scanners/upcoming_meeting_scanner.py`
- [X] T009 [US1] Register `UpcomingMeetingTaskScanner` in `ReminderModuleProvider` in `backend/app/reminder/providers.py` and inject into `ScanAndSendRemindersUseCase`
- [X] T010 [US1] Export `UpcomingMeetingTaskScanner` in `backend/app/reminder/application/scanners/__init__.py` and `backend/app/reminder/application/__init__.py`

**Checkpoint**: User Story 1 hoạt động độc lập và hoàn chỉnh, cung cấp MVP nhắc nhở cuộc họp cơ bản.

---

## Phase 4: User Story 2 - Tự động loại trừ thành viên đã có đơn xin vắng được duyệt hoặc đã đổi ca (Priority: P2)

**Goal**: Tự động nhận biết và bỏ qua không gửi thông báo nhắc nhở cho thành viên đã có đơn xin vắng được duyệt (`ABSENT_EXCUSED`) hoặc đã chuyển sang ca họp khác.

**Independent Test**: Cấu hình buổi họp có thành viên A (`NOT_JOINED`) và thành viên B (`ABSENT_EXCUSED`). Chạy scanner $\rightarrow$ chỉ thành viên A sinh candidate, thành viên B bị loại trừ hoàn toàn.

### Tests for User Story 2

- [X] T011 [P] [US2] Add unit test cases in `backend/tests/unit/test_upcoming_meeting_scanner.py` verifying exclusion of `ABSENT_EXCUSED` and transferred participants

### Implementation for User Story 2

- [X] T012 [US2] Implement absence and transferred participant exclusion logic (`p.status == ParticipantStatus.ABSENT_EXCUSED`) in `UpcomingMeetingTaskScanner` in `backend/app/reminder/application/scanners/upcoming_meeting_scanner.py`

**Checkpoint**: Cả User Story 1 và User Story 2 đều hoạt động độc lập và bảo đảm tính chính xác nghiệp vụ đơn phép.

---

## Phase 5: User Story 3 - Quản trị viên theo dõi trạng thái quét và điều phối nhắc nhở cuộc họp (Priority: P3)

**Goal**: Ban quản trị có thể kích hoạt quét thử nghiệm (dry-run) hoặc quét thật cho toàn bộ cuộc họp qua API quản trị `/api/v1/reminders/trigger` và nhận báo cáo chi tiết.

**Independent Test**: Gọi `POST /api/v1/reminders/trigger?dry_run=true` với quyền Admin $\rightarrow$ nhận kết quả tổng số cuộc họp quét, số nhắc nhở phát sinh với `task_type: "MEETING"`.

### Tests for User Story 3

- [X] T013 [P] [US3] Add integration test for meeting reminders in `ScanAndSendRemindersUseCase` in `backend/tests/unit/test_reminder_use_cases.py`

### Implementation for User Story 3

- [X] T014 [US3] Verify `/api/v1/reminders/trigger` endpoint in `backend/app/reminder/controller.py` handles `TaskType.MEETING` scanning and response reporting end-to-end

**Checkpoint**: Toàn bộ luồng quét tự động và điều phối quản trị qua API đã được xác thực hoàn chỉnh.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Kiểm thử toàn diện, dọn dẹp mã nguồn và xác thực hướng dẫn chạy nhanh

- [X] T015 [P] Run full test suite for reminder module via `pytest backend/tests/unit/test_upcoming_meeting_scanner.py` and `pytest backend/tests/unit/test_reminder_use_cases.py`
- [X] T016 [P] Verify Web UI NotificationFilter displays `MEETING` category items cleanly on `/dashboard/notifications` in `frontend/src/features/notification/components/NotificationFilter.tsx`
- [X] T017 Execute manual validation scenarios in `specs/023-upcoming-meeting-reminder/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không có phụ thuộc, thực hiện ngay lập tức.
- **Foundational (Phase 2)**: Phụ thuộc vào Setup - **BẮT BUỘC** hoàn thành trước khi triển khai các User Story.
- **User Story 1 (Phase 3 - P1 MVP)**: Phụ thuộc vào Phase 2.
- **User Story 2 (Phase 4 - P2)**: Kế thừa logic lọc từ Phase 3.
- **User Story 3 (Phase 5 - P3)**: Phụ thuộc vào việc tích hợp Scanner từ Phase 3 & 4.
- **Polish (Phase 6)**: Phụ thuộc vào tất cả các User Stories hoàn tất.

### Parallel Opportunities

- Các task Setup [P] (T001, T002) có thể chạy song song.
- Các task Foundational [P] (T003, T004, T005) tác động vào các file khác nhau hoặc các hàm riêng biệt trong entity/embed_builder.
- Trong US1: T006 (Test) có thể viết trước song song với việc chuẩn bị T007.
- Trong US2: T011 (Test) có thể chạy song song trước khi hoàn thiện T012.
- Trong Polish: T015 và T016 có thể chạy song song (backend tests và frontend verification).

---

## Parallel Example: User Story 1

```bash
# Khởi tạo kiểm thử độc lập cho User Story 1:
pytest backend/tests/unit/test_upcoming_meeting_scanner.py

# Triển khai scanner và liên kết providers:
Task: "Implement UpcomingMeetingTaskScanner in backend/app/reminder/application/scanners/upcoming_meeting_scanner.py"
Task: "Register UpcomingMeetingTaskScanner in ReminderModuleProvider in backend/app/reminder/providers.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Hoàn thành Phase 1 (Setup) và Phase 2 (Foundational: `TaskType.MEETING`, `create_deadline_reminder`, `build_reminder_embed`).
2. Triển khai Phase 3 (User Story 1): `UpcomingMeetingTaskScanner`, đăng ký Dishka provider, và Unit test.
3. Chạy `pytest backend/tests/unit/test_upcoming_meeting_scanner.py` để kiểm chứng độc lập.
4. **Kiểm thử MVP**: Kích hoạt quét thử nghiệm qua API `/api/v1/reminders/trigger?dry_run=true`.

### Incremental Delivery

1. **Giai đoạn 1**: Hoàn tất US1 (MVP) $\rightarrow$ Thành viên nhận nhắc nhở cuộc họp.
2. **Giai đoạn 2**: Hoàn tất US2 $\rightarrow$ Loại trừ thành viên có đơn xin vắng (`ABSENT_EXCUSED`) hoặc đổi ca.
3. **Giai đoạn 3**: Hoàn tất US3 $\rightarrow$ Xác thực API điều phối và báo cáo quét của Quản trị viên.
4. **Giai đoạn 4**: Polish $\rightarrow$ Kiểm thử hồi quy toàn bộ hệ thống.
