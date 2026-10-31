# Tasks: Chuyển hoàn toàn trường Deadline của Homework sang bảng Assignees & Tích hợp đơn xin hoãn (039-per-assignee-homework-deadline)

**Input**: Design documents from `specs/039-per-assignee-homework-deadline/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/job-contracts.md`, `quickstart.md`)  
**Prerequisites**: `specs/039-per-assignee-homework-deadline/plan.md`, `specs/039-per-assignee-homework-deadline/spec.md`

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Có thể chạy song song (khác file, không phụ thuộc task chưa xong)
- **[Story]**: Gán nhãn User Story tương ứng (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`)
- Mô tả kèm đường dẫn file chính xác

---

## Phase 1: Setup & Foundational (Data Model & Schema Migration)

**Purpose**: Chuyển đổi cấu trúc Database và ORM Models để bảng `homework_assignees` lưu `deadline`, xoá `deadline` khỏi `homeworks`.

- [ ] T001 Tạo migration script SQL hoặc Alembic để thêm cột `deadline TIMESTAMPTZ NULL` vào `homework_assignees`, backfill dữ liệu từ `homeworks.deadline`, cập nhật deadline cho đơn `POSTPONE` đang hiệu lực, đổi `deadline` thành `NOT NULL`, tạo index `ix_homework_assignees_deadline`, và `DROP COLUMN deadline` khỏi bảng `homeworks`
- [ ] T002 Cập nhật `HomeworkModel` và `HomeworkAssigneeModel` trong `backend/app/homework/infrastructure/model.py`: Xoá cột `deadline` khỏi `HomeworkModel`, thêm `deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)` vào `HomeworkAssigneeModel`
- [ ] T003 Cập nhật Entity `Homework` và `HomeworkAssignee` trong `backend/app/homework/domain/entity.py`: Xoá `deadline` khỏi `Homework`, thêm `deadline: datetime` vào `HomeworkAssignee`
- [ ] T004 [P] Định nghĩa Value Object `DueHomeworkAssignment` trong `backend/app/homework/domain/value_objects.py` phục vụ cho checker job

**Checkpoint**: Foundation hoàn tất - schema và domain entities đã sẵn sàng cho việc triển khai User Stories.

---

## Phase 2: User Story 1 - Chuyển đổi Repositories & DTOs cơ bản (Priority: P1) 🎯 MVP

**Goal**: Đảm bảo tầng Data Access và DTOs tương thích với cấu trúc mới: `HomeworkAssigneeRepository` hỗ trợ `deadline`, `HomeworkRepository` không còn phụ thuộc cột `deadline`.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_homework_validation.py` để xác thực các DTOs và models khởi tạo hợp lệ không còn trường `deadline` trên Homework.

- [ ] T005 [US1] Cập nhật `HomeworkAssigneeRepository` trong `backend/app/homework/infrastructure/homework_assignee_repository.py`: Bổ sung methods `assign_users(homework_id, user_ids, deadline)`, `get_user_deadline(homework_id, user_id)`, `update_deadline(homework_id, user_id, new_deadline)`, và `get_by_deadline_date(target_date)`
- [ ] T006 [US1] Cập nhật `HomeworkRepository` trong `backend/app/homework/infrastructure/homework_repository.py`: Loại bỏ các câu truy vấn và cập nhật liên quan đến `HomeworkModel.deadline`, xoá bỏ method cũ `get_by_deadline_date` khỏi homework repo
- [ ] T007 [P] [US1] Cập nhật DTOs trong `backend/app/homework/application/dtos.py`: Điều chỉnh `HomeworkBase`, `HomeworkCreate`, `HomeworkUpdate`, và `HomeworkResponse` để xử lý `deadline` phù hợp
- [ ] T008 [US1] Chạy unit tests DTOs và repositories để xác nhận User Story 1 hoàn thành

**Checkpoint**: MVP Foundation hoàn tất, các thao tác CRUD repository đã chuyển sang `homework_assignees.deadline`.

---

## Phase 3: User Story 2 - Tạo và Quản lý Bài tập với Deadline theo Assignee (Priority: P1)

**Goal**: Khi Admin tạo hoặc phân công bài tập, hạn nộp được lưu trực tiếp vào từng bản ghi `homework_assignees`.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_homework_use_cases.py` để xác nhận bài tập tạo mới ghi nhận đúng deadline vào từng assignee.

- [ ] T009 [US2] Cập nhật `CreateHomeworkUseCase` trong `backend/app/homework/application/create_homework_use_case.py`: Khi tạo bài tập, lưu deadline trực tiếp vào các bản ghi `homework_assignees` thông qua `homework_assignee_repo.assign_users(hw_id, user_ids, data.deadline)`
- [ ] T010 [US2] Cập nhật `UpdateHomeworkUseCase` trong `backend/app/homework/application/update_homework_use_case.py`: Khi cập nhật phân công hoặc hạn nộp, cập nhật deadline tương ứng trong `homework_assignees`
- [ ] T011 [P] [US2] Cập nhật `GetHomeworksUseCase` và `GetHomeworkDetailUseCase` trong `backend/app/homework/application/`: Trả về hạn nộp tổng quan cho Admin view từ `assignees`
- [ ] T012 [US2] Cập nhật unit tests cho Create/Update Homework Use Case trong `backend/tests/unit/`

**Checkpoint**: Tạo và sửa bài tập đã lưu trữ chính xác deadline vào từng assignee.

---

## Phase 4: User Story 3 - Tích hợp Đơn xin hoãn nộp bài tập (`POSTPONE`) (Priority: P1)

**Goal**: Khi học viên tạo đơn xin hoãn (`POSTPONE`), hệ thống tự động cập nhật `deadline` của học viên đó trong `homework_assignees` và lưu `old_deadline` trong payload; khi xoá đơn thì hoàn nguyên.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_permission_strategies.py` để xác nhận `PostponeStrategy` cập nhật và hoàn nguyên `assignee.deadline`.

- [ ] T013 [P] [US3] Cập nhật `PostponePayload` trong `backend/app/permission_request/domain/payloads.py`: Bổ sung trường `old_deadline: datetime | None = None`
- [ ] T014 [US3] Cập nhật `PostponeStrategy` trong `backend/app/permission_request/application/strategies/postpone_strategy.py`:
  - Trong `validate()`: Lấy `current_deadline = self.homework_assignee_repo.get_user_deadline(homework_id, request.user_id)` và kiểm tra hạn xin hoãn không vượt quá 4 ngày so với deadline hiện tại
  - Trong `on_created()`: Ghi nhận `request.payload.old_deadline = current_deadline` và cập nhật `self.homework_assignee_repo.update_deadline(homework_id, user_id, request.payload.start_time)`
  - Trong `on_deleted()`: Nếu có `request.payload.old_deadline`, hoàn nguyên deadline của học viên về `old_deadline`
- [ ] T015 [US3] Cập nhật đăng ký DI trong `backend/app/permission_request/providers.py`: Inject `homework_assignee_repo` vào `PostponeStrategy`
- [ ] T016 [US3] Bổ sung unit tests cho `PostponeStrategy` trong `backend/tests/unit/test_permission_strategies.py` kiểm tra luồng tạo đơn và xoá đơn

**Checkpoint**: Đơn xin hoãn bài tập đã tương tác và cập nhật trực tiếp `assignee.deadline` chính xác.

---

## Phase 5: User Story 4 - Quét Vi phạm Bài tập theo Deadline của từng Assignee (Priority: P1)

**Goal**: `CheckOverdueHomeworkUseCase` quét độc lập theo `homework_assignees.deadline` (mặc định trễ 2 ngày), giải quyết triệt để vấn đề lọt vi phạm sau khi hết hạn hoãn.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py backend/tests/integration/test_homework_quiz_integration.py` để xác nhận học viên A (không hoãn) và học viên B (xin hoãn) được quét độc lập đúng ngày.

- [ ] T017 [US4] Cập nhật `CheckOverdueHomeworkUseCase` trong `backend/app/homework/application/check_overdue_homework_use_case.py`:
  - Khi `target_date is None`: tính `target_date = today_vn - 2 days`
  - Truy vấn `due_assignments = self.homework_assignee_repo.get_by_deadline_date(target_date)`
  - Với mỗi assignment: kiểm tra bài nộp trong DB của user đó với `assignment.deadline` (`submitted_at <= assignment.deadline`)
  - Nếu chưa hoàn thành -> Phát sự kiện `HomeworkOverdueDetected`
- [ ] T018 [US4] Cập nhật event handler `AutomatedViolationHandler` trong `backend/app/violation/application/event_handlers.py`: Tinh gọn logic vì `assignment.deadline` đã là hạn nộp chính thức sau gia hạn
- [ ] T019 [US4] Cập nhật và bổ sung test cases trong `backend/tests/unit/test_homework_checker.py` và `backend/tests/integration/test_homework_quiz_integration.py` kiểm tra quét độc lập từng assignee deadline
- [ ] T020 [US4] Chạy toàn bộ test suites của homework checker để xác nhận tính chính xác

**Checkpoint**: Quét vi phạm bài tập hoạt động chính xác 100% theo từng assignee deadline.

---

## Phase 6: User Story 5 - Hiển thị Deadline cá nhân trên giao diện Học viên & Nhắc việc (Priority: P2)

**Goal**: Học viên xem bài tập cá nhân (`/my-homeworks`) thấy đúng hạn nộp cá nhân của mình; hệ thống nhắc việc quét theo deadline cá nhân.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_reminder_use_cases.py` để xác nhận scanner quét nhắc việc theo deadline cá nhân.

- [ ] T021 [US5] Cập nhật `GetUserHomeworksUseCase` trong `backend/app/homework/application/get_user_homeworks_use_case.py`: Trả về `deadline = assignee.deadline` của học viên đang đăng nhập
- [ ] T022 [US5] Cập nhật `HomeworkScanner` trong `backend/app/reminder/application/scanners/homework_scanner.py`: Quét hạn nộp nhắc việc dựa trên `homework_assignee.deadline` của từng học viên
- [ ] T023 [P] [US5] Rà soát và cập nhật các serializer / DTOs trả về cho Frontend đảm bảo field `deadline` luôn có giá trị hợp lệ từ assignee

**Checkpoint**: Giao diện học viên và hệ thống nhắc việc đều hiển thị và xử lý đồng bộ deadline cá nhân.

---

## Phase 7: Polish, Migration & Regression Verification

**Purpose**: Chạy migration trên môi trường thực tế, kiểm tra toàn diện và xác thực kịch bản quickstart.

- [ ] T024 [P] Rà soát toàn bộ codebase tìm kiếm các tham chiếu `homework.deadline` cũ và cập nhật triệt để (không để sót)
- [ ] T025 Chạy toàn bộ test suite `backend/.venv/bin/pytest` đảm bảo 100% tests liên quan passed
- [ ] T026 Thực thi xác thực theo 6 kịch bản trong `specs/039-per-assignee-homework-deadline/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup & Foundational)**: Không phụ thuộc, bắt đầu ngay.
- **Phase 2 (US1 Repositories & DTOs)**: Phụ thuộc vào Phase 1 (Models & Entities).
- **Phase 3 (US2 Create/Update Homework)**: Phụ thuộc vào Phase 2.
- **Phase 4 (US3 Postpone Strategy)**: Phụ thuộc vào Phase 2.
- **Phase 5 (US4 Overdue Checker)**: Phụ thuộc vào Phase 2, Phase 3, và Phase 4.
- **Phase 6 (US5 Student View & Reminder)**: Phụ thuộc vào Phase 2.
- **Phase 7 (Polish & Regression)**: Phụ thuộc vào tất cả phases hoàn thành.

### Parallel Opportunities
- T003, T004 trong Phase 1 có thể chạy song song.
- T007 trong Phase 2 có thể chạy song song với T005, T006.
- Phase 3 (US2), Phase 4 (US3), và Phase 6 (US5) có thể triển khai song song sau khi Phase 2 hoàn thành.
- T013 có thể làm độc lập với các use case khác.

---

## Implementation Strategy

### MVP First (Phases 1, 2, 3)
1. Chuyển đổi Model và Entity: xoá `deadline` ở Homeworks, thêm `deadline` vào Assignees.
2. Cập nhật `HomeworkAssigneeRepository` và DTOs.
3. Đảm bảo Create/Update Homework lưu `deadline` vào assignees.

### Incremental Delivery
1. Tiếp tục triển khai US3 (`PostponeStrategy` cập nhật `assignee.deadline`).
2. Triển khai US4 (Job quét vi phạm theo `assignee.deadline` trễ 2 ngày).
3. Triển khai US5 (Hiển thị deadline cá nhân cho học viên và scanner nhắc việc).
4. Chạy Phase 7 kiểm thử hồi quy toàn diện.
