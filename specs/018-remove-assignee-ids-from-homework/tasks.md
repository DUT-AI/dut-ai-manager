# Tasks: Loại Bỏ `assignee_ids` Khỏi Entity `Homework`

**Input**: Design documents from `/specs/018-remove-assignee-ids-from-homework/`
**Prerequisites**: [plan.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/018-remove-assignee-ids-from-homework/plan.md), [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/018-remove-assignee-ids-from-homework/spec.md), [data-model.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/018-remove-assignee-ids-from-homework/data-model.md)

## Organization
Tasks được chia theo từng User Story độc lập để có thể kiểm thử và triển khai theo từng giai đoạn rõ ràng.

## Phase 1: Setup & Foundational (Domain & Infrastructure Refactor)

**Purpose**: Làm sạch Aggregate Root `Homework` và cơ chế ánh xạ ORM Model / Repository.

- [x] T001 [P] [US1] Loại bỏ thuộc tính `assignee_ids: list[int] = []` khỏi `Homework(BaseEntity)` trong `backend/app/homework/domain/entity.py`.
- [x] T002 [P] [US1] Xóa bỏ `assignee_ids` khỏi `HomeworkModel.to_entity()` trong `backend/app/homework/infrastructure/model.py`.
- [x] T003 [US1] Xóa bỏ logic phân công (`sync_assignees`, insert `HomeworkAssigneeModel`) khỏi `HomeworkRepository.create()` và `update()` trong `backend/app/homework/infrastructure/homework_repository.py`.
- [x] T004 [P] [US1] Cập nhật Value Object `HomeworkProps` (nếu có) trong `backend/app/homework/domain/value_objects.py`.

---

## Phase 2: User Story 1 - Khởi Tạo & Truy Vấn Bài Tập Tinh Gọn (Priority: P1) 🎯 MVP

**Goal**: Đảm bảo bài tập được tạo và truy vấn độc lập không còn mang theo `assignee_ids`.

- [x] T005 [US1] Cập nhật `backend/app/homework/application/rescan_all_homeworks_use_case.py` không truyền `assignee_ids` khi khởi tạo `Homework`.
- [x] T006 [US1] Cập nhật `backend/app/homework/application/get_user_homeworks_use_case.py` để map DTO không dựa vào `hw.assignee_ids`.

---

## Phase 3: User Story 2 - Quản Lý Phân Công Bài Tập Qua `HomeworkAssigneeRepository` (Priority: P2)

**Goal**: Di chuyển toàn bộ trách nhiệm phân công học viên khi tạo và sửa bài tập sang `HomeworkAssigneeRepository`.

- [x] T007 [US2] Cập nhật `CreateHomeworkUseCase` trong `backend/app/homework/application/create_homework_use_case.py`: Inject `HomeworkAssigneeRepository` và gọi `sync_assignees(homework.id, data.assignee_ids)`.
- [x] T008 [US2] Cập nhật `UpdateHomeworkUseCase` trong `backend/app/homework/application/update_homework_use_case.py`: Inject `HomeworkAssigneeRepository` và gọi `sync_assignees(homework.id, data.assignee_ids)`.
- [x] T009 [US2] Cập nhật Dishka provider trong `backend/app/homework/providers.py` để inject `HomeworkAssigneeRepository` vào `CreateHomeworkUseCase` và `UpdateHomeworkUseCase`.

---

## Phase 4: User Story 3 - Duy Trì Đầy Đủ Logic Các Báo Cáo & Cron Job Quá Hạn (Priority: P3)

**Goal**: Chuyển các Use Case đọc dữ liệu phân công sang gọi `HomeworkAssigneeRepository`.

- [x] T010 [US3] Cập nhật `CheckOverdueHomeworkUseCase` trong `backend/app/homework/application/check_overdue_homework_use_case.py`: Inject `HomeworkAssigneeRepository` và lấy `assigned_uids = homework_assignee_repo.get_assigned_user_ids(homework.id)`.
- [x] T011 [US3] Cập nhật `GetUnsubmittedHomeworkReportUseCase` trong `backend/app/homework/application/get_unsubmitted_homework_report_use_case.py`: Dùng `HomeworkAssigneeRepository` để kiểm tra phân công của học viên.
- [x] T012 [US3] Cập nhật Dishka provider trong `backend/app/homework/providers.py` cho `CheckOverdueHomeworkUseCase` và `GetUnsubmittedHomeworkReportUseCase`.

---

## Phase 5: Verification & Tests

**Goal**: Đảm bảo toàn bộ test suite vượt qua 100%.

- [x] T013 [P] Cập nhật các mock/dữ liệu khởi tạo `Homework` trong `backend/tests/unit/test_homework_*.py`.
- [x] T014 [P] Cập nhật integration tests trong `backend/tests/integration/test_homework_quiz_integration.py`.
- [x] T015 Chạy toàn bộ API test suite: `uv run pytest tests/api/test_homework_api.py -v`.
