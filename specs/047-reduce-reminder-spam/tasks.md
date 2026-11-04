---
description: "Task list for feature 047-reduce-reminder-spam"
---

# Tasks: Tái cấu trúc Nghiệp vụ Nhắc nhở Theo Mốc Đếm Ngược & Loại bỏ Spam Thông báo

**Input**: Design documents from `/specs/047-reduce-reminder-spam/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)  
**Tests**: Automated unit and integration tests with `pytest` for countdown offsets, deduplication, and Zalo channel muting.  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Có thể chạy song song (các file khác nhau, không phụ thuộc vào task chưa hoàn thành).
- **[Story]**: Gắn nhãn User Story (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`).
- Tất cả các task đều có đường dẫn tệp cụ thể.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Khởi tạo cấu hình và chuẩn bị môi trường chạy kiểm thử

- [x] T001 [P] Remove Zalo from _external_channels in backend/app/shared/infrastructure/notification/dispatcher.py to mute Zalo bot without extra config flag
- [x] T002 [P] Verify baseline test suite execution via backend/tests/unit/test_reminder_use_cases.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Chuẩn bị Domain Entities và Enums cốt lõi làm tiền đề cho toàn bộ User Stories

**⚠️ CRITICAL**: Phải hoàn thành Phase này trước khi thực hiện logic quét và điều phối thông báo

- [x] T003 Update ReminderStage Enum in backend/app/reminder/domain/entity.py with active countdown stages (OFFSET_1D, OFFSET_4H, OFFSET_1H) and preserve legacy values (FIXED_0800, FIXED_1200, FIXED_1930, FIXED_2200, OFFSET_2D, OFFSET_12H) for database backward compatibility
- [x] T004 Update is_critical property in backend/app/reminder/domain/entity.py to designate only ReminderStage.OFFSET_1H as critical

**Checkpoint**: Foundation ready - có thể bắt đầu triển khai các User Story độc lập

---

## Phase 3: User Story 1 & 2 - Pure Countdown Offsets & Elimination of Fixed Hours (Priority: P1) 🎯 MVP

**Goal**: Loại bỏ hoàn toàn 4 khung giờ cố định (`08:00`, `12:00`, `19:30`, `22:00`), chuyển toàn bộ hệ thống quét sang 3 mốc đếm ngược chuẩn: `24h` (`OFFSET_1D`), `4h` (`OFFSET_4H`), và `1h` (`OFFSET_1H`).

**Independent Test**:
- Chạy test case kiểm tra `calculate_matching_stages()` vào các khung giờ 08:00, 12:00, 19:30, 22:00 không sinh ra stage nào nếu không trùng mốc đếm ngược.
- Chạy test case với các khoảng cách `24h`, `4h`, `1h` trả về chính xác 1 stage tương ứng.

### Tests for User Story 1 & 2 ⚠️

- [x] T005 [P] [US1] Write unit tests for calculate_matching_stages verifying pure countdown offsets (24h, 4h, 1h) and zero fixed hours generation in backend/tests/unit/test_reminder_use_cases.py

### Implementation for User Story 1 & 2

- [x] T006 [US1] Implement calculate_matching_stages in backend/app/reminder/domain/entity.py to compute only OFFSET_1D (22.0h-26.0h), OFFSET_4H (3.5h-4.5h), and OFFSET_1H (0.5h-1.5h)
- [x] T007 [US1] Update BaseTaskScanner stage delegation in backend/app/reminder/application/scanners/base_scanner.py
- [x] T008 [P] [US1] Review and align HomeworkTaskScanner candidate matching with countdown offsets in backend/app/reminder/application/scanners/homework_scanner.py
- [x] T009 [P] [US1] Review and align DutyTaskScanner candidate matching with countdown offsets in backend/app/reminder/application/scanners/duty_scanner.py
- [x] T010 [P] [US1] Review and align UpcomingMeetingTaskScanner candidate matching with countdown offsets in backend/app/reminder/application/scanners/upcoming_meeting_scanner.py
- [x] T011 [P] [US1] Review and align MeetingEvaluationTaskScanner candidate matching with countdown offsets in backend/app/reminder/application/scanners/meeting_evaluation_scanner.py
- [x] T012 [US1] Update ScanAndSendRemindersUseCase unit tests for countdown offsets in backend/tests/unit/test_reminder_use_cases.py

**Checkpoint**: User Story 1 & 2 hoàn thành - Scheduler chỉ kích hoạt tại 3 mốc đếm ngược, không còn réo chuông vào các giờ cố định cũ.

---

## Phase 4: User Story 3 - Mute Zalo Bot Notification Channel (Priority: P2)

**Goal**: Tắt việc phát thông báo qua Zalo Bot trong bộ điều phối thông báo đa kênh, bảo toàn 100% mã nguồn Zalo Bot Client và Zalo Channel.

**Independent Test**:
- Gửi thông báo qua `UnifiedNotificationDispatcher`, kiểm tra `ZaloBotClient.send_message` không được gọi và Zalo không có trong `_external_channels`, trong khi In-App, Discord DM và Web Push vẫn gửi thành công.

### Tests for User Story 3 ⚠️

- [x] T013 [P] [US3] Write unit test verifying Zalo channel is excluded from UnifiedNotificationDispatcher._external_channels in backend/tests/unit/test_unified_notification_dispatcher.py and test_reminder_use_cases.py

### Implementation for User Story 3

- [x] T014 [US3] Keep ZaloNotificationChannel code and ZaloBotClient intact without config flag dependence in backend/app/shared/infrastructure/notification/zalo_channel.py
- [x] T015 [US3] Update UnifiedNotificationDispatcher in backend/app/shared/infrastructure/notification/dispatcher.py to set _external_channels = [discord, web_push] to mute Zalo notifications

**Checkpoint**: User Story 3 hoàn thành - Zalo Bot không còn bắn tin nhắn làm phiền người dùng.

---

## Phase 5: User Story 4 & 5 - Notification Formatting, Deduplication & Real-Time Exclusion (Priority: P2/P3)

**Goal**: Đảm bảo định dạng thông báo quen thuộc của từng loại nhiệm vụ được bảo toàn, cơ chế Deduplication hoạt động chính xác cho 3 mốc đếm ngược, và các nhiệm vụ đã hoàn thành/miễn trừ lập tức được bỏ qua.

**Independent Test**:
- Kiểm tra nội dung notification tạo ra cho Homework, Duty, Meeting có đầy đủ tiêu đề, hạn chót, liên kết.
- Kiểm tra nhiệm vụ đã nộp hoặc mốc đã gửi trước đó không bị gửi lặp.

### Implementation for User Story 4 & 5

- [x] T016 [P] [US4] Verify ReminderDispatcher payload formatting and urgency coloring in backend/app/reminder/application/reminder_dispatcher.py
- [x] T017 [US5] Verify real-time submission and excuse filtering across scanners in backend/tests/unit/test_reminder_use_cases.py
- [x] T018 [US5] Update integration test for deduplication with countdown stages in backend/tests/integration/test_reminder_integration.py

**Checkpoint**: Toàn bộ User Stories 1, 2, 3, 4, 5 hoạt động đồng bộ và ổn định.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Chạy toàn bộ test suite, kiểm chứng hồi quy và đối chiếu với quickstart guide

- [x] T019 [P] Run full backend reminder test suite via backend/tests/unit/test_reminder_use_cases.py and backend/tests/integration/test_reminder_integration.py
- [x] T020 Validate end-to-end scenarios against specs/047-reduce-reminder-spam/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không có phụ thuộc, có thể bắt đầu ngay lập tức.
- **Foundational (Phase 2)**: Phụ thuộc vào Phase 1 - BLOCK toàn bộ User Stories.
- **User Story 1 & 2 (Phase 3 - MVP)**: Phụ thuộc vào Phase 2.
- **User Story 3 (Phase 4)**: Phụ thuộc vào Phase 1 & 2; có thể chạy song song với Phase 3.
- **User Story 4 & 5 (Phase 5)**: Phụ thuộc vào Phase 3 & 4.
- **Polish (Phase 6)**: Phụ thuộc vào toàn bộ các User Stories hoàn thành.

### Parallel Opportunities

- T001, T002 có thể chạy song song trong Phase 1.
- T008, T009, T010, T011 có thể kiểm tra song song sau khi hoàn thành T006.
- Phase 4 (US3 - Mute Zalo) có thể thực hiện song song với Phase 3 (US1/US2 - Countdown Stages) vì tác động vào 2 module file hoàn toàn độc lập (`shared/notification/` vs `reminder/domain/`).

---

## Parallel Example: User Story 1 & User Story 3

```bash
# Developer A hoặc Luồng 1 thực hiện US1 (Countdown Offsets):
Task: T006 Implement calculate_matching_stages in backend/app/reminder/domain/entity.py
Task: T008 Review and align HomeworkTaskScanner in backend/app/reminder/application/scanners/homework_scanner.py

# Developer B hoặc Luồng 2 thực hiện US3 (Mute Zalo Bot):
Task: T014 Update ZaloNotificationChannel.send in backend/app/shared/infrastructure/notification/zalo_channel.py
Task: T015 Update UnifiedNotificationDispatcher in backend/app/shared/infrastructure/notification/dispatcher.py
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2)

1. Hoàn thành Phase 1 & Phase 2.
2. Hoàn thành Phase 3 (US1 & US2): Chuyển sang 3 mốc đếm ngược `24h`, `4h`, `1h`, loại bỏ 4 khung giờ cố định.
3. Chạy test xác nhận MVP: Ngay lập tức giảm 70% lượng thông báo thừa.

### Incremental Delivery

1. MVP (US1 + US2) ➔ Triệt tiêu các khung giờ cố định và chuyển sang đếm ngược.
2. Thêm US3 ➔ Tắt kênh Zalo Bot để không làm phiền ứng dụng Zalo cá nhân.
3. Thêm US4 + US5 ➔ Bảo toàn định dạng và hoàn thiện chống trùng lặp.
4. Chạy Phase 6 Polish ➔ Đảm bảo 100% tests passed.
