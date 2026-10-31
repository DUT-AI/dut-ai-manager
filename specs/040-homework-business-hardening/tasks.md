# Tasks: Củng Cố Toàn Diện Nghiệp Vụ Bài Tập (Homework Business Hardening)

**Input**: Design documents from `specs/040-homework-business-hardening/`  
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/  

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to ([US1], [US2], [US3])
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Xác minh môi trường và công cụ kiểm thử trước khi thực thi

- [X] T001 Kiểm tra môi trường virtualenv và chạy bộ unit test hiện tại qua `backend/.venv/bin/pytest backend/tests/unit`

---

## Phase 2: Foundational (Prerequisites)

**Purpose**: Đảm bảo các dependency và repository cần thiết sẵn sàng cho các user story

- [X] T002 Rà soát các Dishka providers trong `backend/app/homework/providers.py` và `backend/app/permission_request/providers.py`

---

## Phase 3: User Story 1 - Nhắc nhở bài tập chính xác cho học sinh chưa hoàn thành đủ bài (Priority: P1) 🎯 MVP

**Goal**: Nâng cấp `HomeworkTaskScanner` sử dụng `Homework.evaluate_submissions()`, đảm bảo học sinh nộp thiếu Coding hoặc Game vẫn nhận được thông báo nhắc nhở tự động trước hạn nộp cá nhân.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_reminder_use_cases.py` xác nhận học sinh mới chỉ làm Game hoặc mới nộp 1 bài Coding con vẫn được đưa vào danh sách ứng viên nhắc nhở.

### Tests for User Story 1
- [X] T003 [P] [US1] Viết unit tests kiểm tra `HomeworkTaskScanner` với các kịch bản: nộp thiếu Coding, nộp thiếu Game, nộp bài Coding bị Failed trong `backend/tests/unit/test_reminder_use_cases.py`

### Implementation for User Story 1
- [X] T004 [US1] Cập nhật phương thức `scan_pending_tasks` trong `backend/app/reminder/application/scanners/homework_scanner.py` sử dụng `hw.evaluate_submissions(submissions, deadline=hw_deadline_dt).is_submitted` thay vì `if submissions: continue`
- [X] T005 [US1] Chạy lại unit test `test_reminder_use_cases.py` xác nhận User Story 1 hoàn thành và vượt qua 100%

**Checkpoint**: User Story 1 hoàn tất độc lập — hệ thống nhắc nhở không còn bỏ sót học sinh chưa hoàn thành trọn vẹn bài tập.

---

## Phase 4: User Story 2 - Quản lý và đối soát bài tập con từ nguồn Quiz API chuẩn xác (Priority: P2)

**Goal**: Tích hợp `QuizApiClient.get_lesson_exercises(slug)` vào `CheckOverdueHomeworkUseCase` và `GetHomeworkSubmissionStatusUseCase`, hiển thị đầy đủ danh mục bài con ngay cả khi chưa có ai nộp và quét quá hạn chính xác.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py` xác nhận việc đối soát bài tập con sử dụng danh mục chính thức từ Quiz API (và fallback an toàn khi lỗi mạng).

### Tests for User Story 2
- [X] T006 [P] [US2] Viết unit tests cho `CheckOverdueHomeworkUseCase` với mock `quiz_api.get_lesson_exercises` và kịch bản fallback trong `backend/tests/unit/test_homework_checker.py`

### Implementation for User Story 2
- [X] T007 [US2] Cập nhật constructor và logic đối soát bài tập con trong `backend/app/homework/application/check_overdue_homework_use_case.py` để inject `quiz_api: QuizApiClient`, gọi `get_lesson_exercises(slug)` kèm cơ chế fallback từ submissions
- [X] T008 [US2] Cập nhật Dishka provider `get_check_overdue_use_case` trong `backend/app/homework/providers.py` để inject `quiz_api: QuizApiClient`
- [X] T009 [US2] Cập nhật `backend/app/homework/application/get_homework_submission_status_use_case.py` tích hợp `quiz_api.get_lesson_exercises(homework.slug)` để hiển thị danh mục bài con ngay cả khi chưa có bài nộp nào
- [X] T010 [US2] Chạy bộ test kiểm tra bài tập qua `backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py` và `backend/tests/api/test_homework_api.py`

**Checkpoint**: User Story 2 hoàn tất độc lập — danh mục bài tập con hiển thị đầy đủ và việc quét quá hạn đối soát chính xác theo danh sách thực tế của Quiz.

---

## Phase 5: User Story 3 - Kiểm soát chặt chẽ tính hợp lệ của đơn xin hoãn bài tập (Priority: P3)

**Goal**: Củng cố `PostponeStrategy.validate()`: chặn hoãn quá khứ, chặn bài đã quá hạn, chặn bài đã nộp xong; hỗ trợ hoãn tích luỹ nhiều lần nối tiếp (mỗi lần <= 4 ngày so với deadline hiện tại).

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_permission_strategies.py -k "postpone"` xác nhận từ chối mọi đơn hoãn không hợp lệ và chấp thuận đơn hoãn tích luỹ hợp lệ.

### Tests for User Story 3
- [X] T011 [P] [US3] Viết unit tests cho `PostponeStrategy.validate` trong `backend/tests/unit/test_permission_strategies.py` kiểm tra 5 kịch bản: hoãn quá khứ, bài đã quá hạn, bài đã nộp xong, hoãn lần 1 hợp lệ, hoãn tích luỹ lần 2 hợp lệ

### Implementation for User Story 3
- [X] T012 [US3] Cập nhật constructor của `PostponeStrategy` trong `backend/app/permission_request/application/strategies/postpone_strategy.py` để inject `homework_submission_repo: HomeworkSubmissionRepository`
- [X] T013 [US3] Cập nhật Dishka provider cho `PostponeStrategy` trong `backend/app/permission_request/providers.py` để inject `homework_submission_repo: HomeworkSubmissionRepository`
- [X] T014 [US3] Cập nhật logic `validate()` trong `backend/app/permission_request/application/strategies/postpone_strategy.py` thực thi các rào chắn kiểm tra (`extended_deadline > now`, `current_deadline > now`, `not is_submitted`, khoảng cách hoãn tích luỹ `<= 4 ngày`)
- [X] T015 [US3] Chạy unit tests trong `backend/tests/unit/test_permission_strategies.py` xác nhận 100% test cases của User Story 3 vượt qua

**Checkpoint**: User Story 3 hoàn tất độc lập — quy trình tạo đơn hoãn được bảo vệ chống gian lận và hỗ trợ hoãn tích luỹ đúng quy chế.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Kiểm thử toàn diện hệ thống, kiểm tra linter và đảm bảo không có lỗi hồi quy

- [X] T016 Chạy toàn bộ test suites `backend/.venv/bin/pytest backend/tests/unit backend/tests/integration backend/tests/api/test_homework_api.py`
- [X] T017 Kiểm tra linter qua `backend/.venv/bin/ruff check backend/app/reminder backend/app/homework backend/app/permission_request`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Không có phụ thuộc, chạy đầu tiên.
- **Foundational (Phase 2)**: Phụ thuộc vào Phase 1.
- **User Stories (Phase 3 -> 5)**: Chạy tuần tự theo mức độ ưu tiên P1 -> P2 -> P3 (mỗi Story là một phần chức năng độc lập).
- **Polish (Phase 6)**: Chạy sau khi hoàn tất cả 3 User Stories.

### Parallel Opportunities
- T003 [P] [US1], T006 [P] [US2], T011 [P] [US3] có thể viết test độc lập trên các file test khác nhau.
- Các User Story tác động lên các module khác nhau (`reminder`, `homework`, `permission_request`), độc lập và không gây xung đột mã nguồn.
