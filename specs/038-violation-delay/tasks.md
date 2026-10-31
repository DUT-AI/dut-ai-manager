# Tasks: Lùi thời điểm quét vi phạm thêm 2 ngày (038-violation-delay)

**Input**: Design documents from `specs/038-violation-delay/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/job-contracts.md`, `quickstart.md`)  
**Prerequisites**: `specs/038-violation-delay/plan.md`, `specs/038-violation-delay/spec.md`

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Có thể chạy song song (khác file, không phụ thuộc task chưa xong)
- **[Story]**: Gán nhãn User Story tương ứng (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Mô tả kèm đường dẫn file chính xác

---

## Phase 1: Setup & Constants (Shared Infrastructure)

**Purpose**: Thiết lập các hằng số nghiệp vụ độ trễ quét vi phạm và thời hạn đánh giá tại tầng Domain

- [X] T001 [P] Tạo file constants chung trong violation domain `backend/app/violation/domain/constants.py` định nghĩa `DEFAULT_VIOLATION_CHECK_DELAY_DAYS = 2`
- [X] T002 [P] Tạo file constants trong homework domain `backend/app/homework/domain/constants.py` định nghĩa `HOMEWORK_VIOLATION_CHECK_DELAY_DAYS = 2`
- [X] T003 [P] Tạo file constants trong meeting domain `backend/app/meeting/domain/constants.py` định nghĩa `MEETING_ATTENDANCE_CHECK_DELAY_DAYS = 2`, `MEETING_EVALUATION_DEADLINE_HOURS = 72`, `MEETING_EVALUATION_SCAN_WINDOW_DAYS = 9`
- [X] T004 [P] Tạo file constants trong duty domain `backend/app/duty/domain/constants.py` định nghĩa `DUTY_VIOLATION_CHECK_DELAY_DAYS = 2`

---

## Phase 2: Foundational (Domain Exports & Clean Architecture)

**Purpose**: Xuất khẩu các hằng số qua `__init__.py` của từng domain tương ứng, chuẩn bị nền tảng cho Use Cases

- [X] T005 [P] Re-export constants trong `backend/app/violation/domain/__init__.py`, `backend/app/homework/domain/__init__.py`, `backend/app/meeting/domain/__init__.py`, và `backend/app/duty/domain/__init__.py`

**Checkpoint**: Nền tảng hằng số hoàn tất - các User Stories có thể được triển khai độc lập

---

## Phase 3: User Story 1 - Quét vi phạm bài tập trễ 2 ngày & phạt bài tập trễ deadline (Priority: P1) 🎯 MVP

**Goal**: Job kiểm tra bài tập khi chạy tự động (`target_date is None`) sẽ quét bài tập có deadline là `today - 2 ngày`. Chỉ những bài nộp có `submitted_at <= deadline` mới hợp lệ; nộp sau deadline hoặc chưa nộp đều bị tạo vi phạm. Khi truyền `target_date` cụ thể thì quét đúng ngày đó.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py` để xác nhận logic delay 2 ngày và phạt task trễ deadline hoạt động chính xác.

- [X] T006 [P] [US1] Cập nhật và bổ sung test cases trong `backend/tests/unit/test_homework_checker.py` kiểm tra: khi `target_date is None` use case tự động quét `today_vn - 2 ngày`, và xác nhận học viên nộp sau deadline vẫn bị tạo vi phạm
- [X] T007 [US1] Cập nhật `CheckOverdueHomeworkUseCase` trong `backend/app/homework/application/check_overdue_homework_use_case.py` để tính `target_date = today_vn - timedelta(days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS)` khi `target_date is None`, và đảm bảo chỉ chấp nhận bài nộp trước hoặc đúng deadline (`submitted_at <= deadline`)
- [X] T008 [US1] Chạy `backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py` để xác thực User Story 1 hoàn thành và pass 100%

**Checkpoint**: User Story 1 hoàn thành và có thể chạy/test độc lập (MVP)

---

## Phase 4: User Story 2 - Quét vi phạm điểm danh cuộc họp trễ 2 ngày (Priority: P1)

**Goal**: Job kiểm tra điểm danh cuộc họp khi chạy tự động (`target_date is None`) sẽ quét các buổi họp diễn ra vào `today - 2 ngày`. Người tham gia vắng không phép hoặc trễ không phép tại buổi họp ngày đó đều bị tạo vi phạm.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_meeting_use_cases.py` để xác nhận logic delay 2 ngày của điểm danh họp.

- [X] T009 [P] [US2] Cập nhật và bổ sung test cases trong `backend/tests/unit/test_meeting_use_cases.py` kiểm tra: khi `target_date is None` use case tự động quét `today_vn - 2 ngày`, và khi truyền `target_date` thì quét đúng ngày chỉ định
- [X] T010 [US2] Cập nhật `CheckMeetingAttendanceUseCase` trong `backend/app/meeting/application/check_meeting_attendance_use_case.py` để tính `target_date = today_vn - timedelta(days=MEETING_ATTENDANCE_CHECK_DELAY_DAYS)` khi `target_date is None`
- [X] T011 [US2] Chạy `backend/.venv/bin/pytest backend/tests/unit/test_meeting_use_cases.py` để xác thực User Story 2 hoàn thành và pass 100%

**Checkpoint**: User Story 1 và User Story 2 đều hoạt động độc lập và ổn định

---

## Phase 5: User Story 3 - Quét vi phạm trực nhật phòng Lab trễ 2 ngày (Priority: P1)

**Goal**: Job kiểm tra trực nhật khi chạy tự động (`target_date is None`) sẽ quét các ca trực nhật diễn ra vào `today - 2 ngày`. Ca trực chưa nộp minh chứng trước 22:00 ngày trực sẽ bị xử lý vi phạm, không gia hạn nộp bù sau ngày trực.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_duty_use_cases.py` để xác nhận logic delay 2 ngày của trực nhật.

- [X] T012 [P] [US3] Cập nhật và bổ sung test cases trong `backend/tests/unit/test_duty_use_cases.py` kiểm tra: khi `target_date is None` use case tự động quét `today_vn - 2 ngày`, và ca trực quá hạn bị tạo vi phạm chính xác
- [X] T013 [US3] Cập nhật `CheckOverdueDutiesUseCase` trong `backend/app/duty/application/check_overdue_duties_use_case.py` để tính `target_date = today_vn - timedelta(days=DUTY_VIOLATION_CHECK_DELAY_DAYS)` khi `target_date is None`
- [X] T014 [US3] Chạy `backend/.venv/bin/pytest backend/tests/unit/test_duty_use_cases.py` để xác thực User Story 3 hoàn thành và pass 100%

**Checkpoint**: User Story 1, 2, và 3 đều hoạt động trơn tru

---

## Phase 6: User Story 4 - Quét vi phạm đánh giá cuộc họp sau 72h (Priority: P2)

**Goal**: Job kiểm tra đánh giá cuộc họp (`CheckEvaluationDeadlineJobUseCase`) quét các buổi học kết thúc quá 72 giờ (`now - timedelta(hours=72)`) với cửa sổ quét 9 ngày (`now - timedelta(days=9)`). Cập nhật chuỗi lý do vi phạm thành "trong vòng 72h".

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_meeting_evaluation.py` để xác nhận mốc 72h và thông điệp lý do vi phạm.

- [X] T015 [P] [US4] Cập nhật các test cases trong `backend/tests/unit/test_meeting_evaluation.py` với mốc thời gian 72h và kiểm tra assertion thông điệp lý do vi phạm "trong vòng 72h"
- [X] T016 [US4] Cập nhật `CheckEvaluationDeadlineJobUseCase` trong `backend/app/meeting/application/check_evaluation_deadline_job_use_case.py` sử dụng `MEETING_EVALUATION_DEADLINE_HOURS = 72`, `MEETING_EVALUATION_SCAN_WINDOW_DAYS = 9` và cập nhật câu chữ lý do vi phạm thành "trong vòng 72h"
- [X] T017 [US4] Chạy `backend/.venv/bin/pytest backend/tests/unit/test_meeting_evaluation.py` để xác thực User Story 4 hoàn thành và pass 100%

**Checkpoint**: Toàn bộ 4 User Stories đã hoàn thành và test độc lập thành công

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Đồng bộ thông tin mô tả log trong Job wrappers, Scheduler và kiểm thử hồi quy toàn diện

- [X] T018 [P] Rà soát và cập nhật log messages / descriptions trong `backend/app/jobs/homework_checker_job.py`, `backend/app/jobs/meeting_checker_job.py`, `backend/app/jobs/duty_checker_job.py`, `backend/app/jobs/meeting_evaluation_checker_job.py`, và `backend/app/core/scheduler.py`
- [X] T019 Chạy toàn bộ test suite `backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py backend/tests/unit/test_meeting_use_cases.py backend/tests/unit/test_duty_use_cases.py backend/tests/unit/test_meeting_evaluation.py` đảm bảo 100% passed
- [X] T020 Thực thi quy trình kiểm thử nghiệm thu theo kịch bản trong `specs/038-violation-delay/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup & Constants)**: Không phụ thuộc, có thể bắt đầu ngay.
- **Phase 2 (Foundational)**: Phụ thuộc vào Phase 1.
- **Phase 3+ (User Stories)**: Phụ thuộc vào Phase 2 hoàn thành.
  - Các User Story có thể thực thi tuần tự theo độ ưu tiên (US1 🎯 MVP → US2 → US3 → US4) hoặc song song vì các domain (Homework, Meeting, Duty) độc lập với nhau.
- **Phase 7 (Polish)**: Phụ thuộc vào tất cả User Stories hoàn thành.

### Parallel Opportunities
- Các task T001, T002, T003, T004 trong Phase 1 có thể chạy song song vì ở các file domain khác nhau.
- Các task kiểm thử T006, T009, T012, T015 có thể viết song song trước khi triển khai use cases.
- US1, US2, US3, US4 sửa đổi các file use case độc lập trong các bounded contexts riêng biệt, có thể phát triển song song.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Hoàn thành Phase 1 & Phase 2 (Constants).
2. Thực hiện Phase 3 (US1 - Homework Check Delay 2 ngày & trễ deadline).
3. Chạy `pytest backend/tests/unit/test_homework_checker.py` để kiểm thử MVP.

### Incremental Delivery
1. Triển khai tiếp US2 (Meeting Attendance Check Delay 2 ngày) $\rightarrow$ Test US2.
2. Triển khai tiếp US3 (Duty Check Delay 2 ngày) $\rightarrow$ Test US3.
3. Triển khai tiếp US4 (Meeting Evaluation Check 72h) $\rightarrow$ Test US4.
4. Chạy Phase 7 (Polish & Full Regression) để xác nhận hệ thống hoàn toàn ổn định.
