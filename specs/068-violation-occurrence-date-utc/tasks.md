# Tasks: Chuẩn Hóa Thời Gian Xảy Ra Vi Phạm Tự Động Theo UTC

**Input**: Design documents from `/specs/068-violation-occurrence-date-utc/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)  
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Có thể chạy song song (các file khác nhau, không phụ thuộc vào task chưa hoàn thành)
- **[Story]**: Gắn với User Story tương ứng (`[US1]`, `[US2]`, `[US3]`)
- Mô tả kèm đường dẫn file chính xác

---

## Phase 1: Setup & Environment Consistency

**Purpose**: Đảm bảo môi trường kiểm thử và các helper chuyển đổi timezone UTC sẵn sàng.

- [X] T001 Verify timezone utility functions (`ensure_utc`, `parse_to_utc`) in `backend/app/shared/domain/datetime_types.py`
- [X] T002 [P] Create initial test suite file for violation occurrence dates in `backend/tests/unit/test_violation_occurrence_date.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cập nhật hạ tầng Domain Events và Repository bounds để làm nền tảng cho tất cả các user stories.

**⚠️ CRITICAL**: Phải hoàn thành trước khi cập nhật use cases và event handlers.

- [X] T003 Cập nhật `ParticipantAbsenceRecorded` domain event thêm trường `start_time: datetime | None = None` trong `backend/app/meeting/domain/events.py`
- [X] T004 [P] Cập nhật `HomeworkOverdueDetected` domain event thêm trường `deadline: datetime | None = None` trong `backend/app/homework/domain/value_objects.py`
- [X] T005 [P] Chuẩn hóa khoảng lọc ngày `get_by_user_and_date` trong `backend/app/violation/infrastructure/repository.py` để `start` và `end` luôn mang `tzinfo=UTC` khi `target_date` là UTC datetime

**Checkpoint**: Foundation ready - các Domain Event và Repository đã sẵn sàng nhận mốc thời gian UTC chuẩn.

---

## Phase 3: User Story 1 - Vi phạm Vắng sinh hoạt & Đi trễ ghi nhận chính xác thời gian xảy ra (Priority: P1) 🎯 MVP

**Goal**: Khi phát hiện vắng họp hoặc đi trễ, vi phạm tạo ra có trường `date` phản ánh chính xác thời gian bắt đầu buổi họp (`meeting.start_time`) hoặc thời gian quẹt thẻ check-in thực tế (`check_in_at`) dưới chuẩn timezone-aware UTC.

**Independent Test**: Kích hoạt `CheckMeetingAttendanceUseCase` cho buổi họp bắt đầu lúc 18:00 UTC+7 (11:00 UTC). Kiểm tra vi phạm vắng có `date == 11:00 UTC`. Phát sự kiện đi trễ với `check_in_at = 11:15 UTC`, kiểm tra vi phạm đi trễ có `date == 11:15 UTC`.

### Implementation for User Story 1

- [X] T006 [US1] Cập nhật `CheckMeetingAttendanceUseCase.execute` để truyền `start_time=meeting.start_time` khi phát tán `ParticipantAbsenceRecorded` trong `backend/app/meeting/application/check_meeting_attendance_use_case.py`
- [X] T007 [US1] Cập nhật `AutomatedViolationHandler._handle_meeting_absence` gán `date=ensure_utc(event.start_time)` nếu có, fallback về `datetime.now(UTC)` trong `backend/app/violation/application/event_handlers.py`
- [X] T008 [US1] Cập nhật `AutomatedViolationHandler._handle_meeting_late` gán `date=ensure_utc(event.check_in_at)` thay vì `datetime.now(UTC)` trong `backend/app/violation/application/event_handlers.py`
- [X] T009 [P] [US1] Cập nhật `PermissionViolationHandler.handle` để gán `date=ensure_utc(event.start_time)` nếu có, fallback về `datetime.now(UTC)` trong `backend/app/violation/permission_handler.py`
- [X] T010 [US1] Thêm unit test xác minh vi phạm vắng họp và đi trễ mang `date` chuẩn UTC theo thời gian diễn ra buổi họp trong `backend/tests/unit/test_violation_occurrence_date.py`

**Checkpoint**: User Story 1 hoàn thành độc lập và kiểm thử đạt 100%.

---

## Phase 4: User Story 2 - Vi phạm Trực nhật, Quá hạn bài tập & Đánh giá buổi học ghi nhận đúng mốc hạn (Priority: P2)

**Goal**: Đảm bảo các vi phạm do quá hạn nộp bài tập, bỏ trực nhật, hoặc quên đánh giá 24h ghi nhận đúng mốc hạn chót (`assignment.deadline`, `meeting.end_time`, `duty_date 23:59:59 VN`) theo UTC.

**Independent Test**: Chạy `CheckOverdueHomeworkUseCase` với deadline `2026-11-10 16:59:00 UTC`. Vi phạm tạo ra phải có `date == 2026-11-10 16:59:00 UTC`. Chạy `CheckEvaluationDeadlineJobUseCase`, vi phạm có `date == meeting.end_time + 24h`.

### Implementation for User Story 2

- [X] T011 [US2] Cập nhật `CheckOverdueHomeworkUseCase.execute` để truyền `deadline=assignment.deadline` khi phát tán `HomeworkOverdueDetected` trong `backend/app/homework/application/check_overdue_homework_use_case.py`
- [X] T012 [US2] Cập nhật `AutomatedViolationHandler._handle_homework_overdue` gán `date=ensure_utc(event.deadline)` nếu có, fallback về `datetime.now(UTC)` trong `backend/app/violation/application/event_handlers.py`
- [X] T013 [US2] Cập nhật `CheckOverdueDutiesUseCase.execute` để tính toán `occurrence_date` (dựa trên `meeting.end_time` hoặc 23:59:59 của `duty.duty_date` theo giờ VN chuyển UTC) và truyền vào `create_violation_use_case.execute` trong `backend/app/duty/application/check_overdue_duties_use_case.py`
- [X] T014 [US2] Cập nhật `CheckEvaluationDeadlineJobUseCase._check_trainees` và `_check_trainers` để gán `date=ensure_utc(meeting.end_time) + timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)` trong `backend/app/meeting/application/check_evaluation_deadline_job_use_case.py`
- [X] T015 [US2] Thêm unit test xác minh vi phạm bài tập, trực nhật và đánh giá 24h mang `date` chuẩn UTC theo mốc hạn chót trong `backend/tests/unit/test_violation_occurrence_date.py`

**Checkpoint**: User Stories 1 và 2 đều hoạt động độc lập và đạt chuẩn.

---

## Phase 5: User Story 3 - Hiển thị đúng múi giờ địa phương trên UI & Kiểm tra hợp đồng API (Priority: P3)

**Goal**: Đảm bảo API trả về trường `date` dưới dạng chuẩn ISO 8601 UTC (`Z` / `+00:00`) và UI hiển thị chính xác theo local time của client (Việt Nam UTC+7).

**Independent Test**: Gọi API `GET /api/v1/violations` kiểm tra trường `date` trả về kết thúc bằng `Z` hoặc `+00:00`. Kiểm tra component `ViolationTable.tsx` hiển thị đúng `DD/MM/YYYY HH:mm` qua `dayjs(date)`.

### Implementation for User Story 3

- [X] T016 [US3] Kiểm tra và xác nhận serializing của `date` trong `backend/app/violation/schemas.py` trả về chuẩn ISO 8601 timezone-aware
- [X] T017 [P] [US3] Kiểm tra component `ViolationTable.tsx` và `ViolationMobileList.tsx` trong `frontend/src/features/violations/components/` để đảm bảo dùng `dayjs(record.date).format('DD/MM/YYYY HH:mm')` không bị lỗi NaN hoặc lệch múi giờ
- [X] T018 [US3] Thêm integration test cho API danh sách vi phạm `GET /api/v1/violations` xác nhận định dạng response UTC trong `backend/tests/test_violation.py`

**Checkpoint**: Toàn bộ hệ thống từ Backend đến Frontend hiển thị đồng bộ mốc thời gian vi phạm theo local timezone của người dùng.

---

## Phase 6: Polish, Regression & Quickstart Validation

**Purpose**: Đảm bảo toàn bộ test suites hiện có không bị regression và tuân thủ tuyệt đối Constitution.

- [X] T019 [P] Chạy toàn bộ test suite của violation, meeting, homework và duty: `pytest backend/tests/`
- [X] T020 [P] Chạy linter kiểm tra naive datetime: `ruff check backend/app`
- [X] T021 [P] Chạy frontend build kiểm tra types: `cd frontend && npm run build`
- [X] T022 Thực hiện xác thực các kịch bản kiểm thử theo `specs/068-violation-occurrence-date-utc/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Không phụ thuộc, thực hiện đầu tiên.
- **Phase 2 (Foundational)**: Phụ thuộc vào Phase 1. **BẮT BUỘC HOÀN THÀNH** trước khi triển khai các User Story vì thay đổi cấu trúc Domain Event.
- **Phase 3 (User Story 1 - P1)**: Phụ thuộc vào Phase 2. Đóng vai trò MVP.
- **Phase 4 (User Story 2 - P2)**: Phụ thuộc vào Phase 2. Có thể triển khai song song hoặc sau Phase 3.
- **Phase 5 (User Story 3 - P3)**: Phụ thuộc vào dữ liệu sinh ra từ Phase 3/4.
- **Phase 6 (Polish)**: Phụ thuộc vào tất cả các story trước đó.

### User Story Dependencies
- **User Story 1 (P1)**: Sau Phase 2, độc lập hoàn toàn với US2/US3.
- **User Story 2 (P2)**: Sau Phase 2, độc lập hoàn toàn với US1.
- **User Story 3 (P3)**: Có thể xác thực ngay sau khi US1 hoặc US2 hoàn thành.

---

## Parallel Opportunities

- **T003, T004, T005**: Có thể chỉnh sửa song song trong Phase 2 vì nằm ở 3 file/module khác nhau (`meeting/domain/events.py`, `homework/domain/value_objects.py`, `violation/infrastructure/repository.py`).
- **T009**: Có thể làm song song với T006, T007 trong Phase 3.
- **T017**: Có thể rà soát song song với các task backend.
- **T019, T020, T021**: Chạy đồng thời trong giai đoạn Polish.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Hoàn thành Phase 1 & Phase 2 (Foundational Events & Repository).
2. Hoàn thành Phase 3 (User Story 1: Vắng sinh hoạt & Đi trễ).
3. Chạy test `test_violation_occurrence_date.py` xác nhận MVP hoạt động hoàn hảo.

### Incremental Delivery
1. Foundation (Phase 1, 2) →
2. Điểm danh & Đi trễ (Phase 3 - US1) →
3. Bài tập, Trực nhật & Đánh giá 24h (Phase 4 - US2) →
4. Kiểm định API & Frontend UI (Phase 5 - US3) →
5. Regression test & Validation (Phase 6).
