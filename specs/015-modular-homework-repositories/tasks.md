# Tasks: Tách Biệt Các Repository Trong Module Homework & Tối Ưu SQL Join Cho Assignee

**Input**: Design documents from `specs/015-modular-homework-repositories/`
**Prerequisites**: [plan.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/015-modular-homework-repositories/plan.md), [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/015-modular-homework-repositories/spec.md), [research.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/015-modular-homework-repositories/research.md), [data-model.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/015-modular-homework-repositories/data-model.md), [quickstart.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/015-modular-homework-repositories/quickstart.md)

## Phase 1: Setup (Preparation)

**Purpose**: Chuẩn bị cấu trúc thư mục và xác nhận môi trường trước khi phân rã repository.

- [X] T001 Verify baseline test suite passes with 30/30 homework tests in backend/tests/api/test_homework_api.py

---

## Phase 2: Foundational (Tách 3 Repositories Đơn Nhiệm)

**Purpose**: Xây dựng 3 tệp repository độc lập, mỗi repository quản lý đúng 1 bảng dữ liệu, tuân thủ Nguyên tắc I và VII của Constitution v1.5.0.

- [X] T002 [P] Create HomeworkAssigneeRepository in backend/app/homework/infrastructure/homework_assignee_repository.py with sync_assignees, get_assigned_user_ids, get_assigned_homework_ids, add_assignees, remove_assignees
- [X] T003 [P] Create HomeworkSubmissionRepository in backend/app/homework/infrastructure/homework_submission_repository.py with add_submission, get_submissions_by_user, get_user_submissions_for_homeworks, get_all_submissions, has_valid_submission, get_submissions_by_homework, find_submission_match, update_submission, get_submissions_by_exercise, get_submitted_exercise_ids
- [X] T004 Create HomeworkRepository in backend/app/homework/infrastructure/homework_repository.py with CRUD operations on HomeworkModel (get_all, get_paged, get_by_id, create, update, delete_by_id, restore, get_by_slug, get_by_deadline_date) and delegate assignee persistence via direct query
- [X] T005 Create backend/app/homework/infrastructure/__init__.py re-exporting HomeworkRepository, HomeworkSubmissionRepository, and HomeworkAssigneeRepository

**Checkpoint**: 3 Repositories độc lập đã được tạo và sẵn sàng inject.

---

## Phase 3: User Story 1 - Tách Biệt Các Repository Đơn Nhiệm Trong Module Homework (Priority: P1) 🎯 MVP

**Goal**: Cập nhật các Use Case và Dishka provider để inject đúng các Repository đơn nhiệm, loại bỏ phụ thuộc vào repository gộp cũ.

**Independent Test**: Các Use Case chỉ thao tác submission (như `GetUserHomeworkSubmissionsUseCase`) hay CRUD bài tập hoạt động độc lập và pass unit tests.

- [X] T006 [P] [US1] Update Dishka provider in backend/app/homework/providers.py to register HomeworkRepository, HomeworkSubmissionRepository, and HomeworkAssigneeRepository at Scope.REQUEST
- [X] T007 [P] [US1] Update backend/app/homework/application/get_user_homework_submissions_use_case.py to inject HomeworkSubmissionRepository
- [X] T008 [P] [US1] Update backend/app/homework/application/create_homework_use_case.py and update_homework_use_case.py to inject HomeworkRepository and HomeworkAssigneeRepository
- [X] T009 [P] [US1] Update backend/app/homework/application/record_submission_use_case.py and sync_homework_use_case.py to inject HomeworkRepository and HomeworkSubmissionRepository
- [X] T010 [P] [US1] Update backend/app/homework/application/get_homework_submission_status_use_case.py to inject HomeworkRepository, HomeworkSubmissionRepository, and HomeworkAssigneeRepository
- [X] T011 [P] [US1] Update backend/app/homework/application/check_overdue_homework_use_case.py and rescan_all_homeworks_use_case.py to inject HomeworkRepository and HomeworkSubmissionRepository
- [X] T012 [P] [US1] Update backend/app/homework/application/event_handlers.py to inject HomeworkRepository and HomeworkSubmissionRepository
- [X] T013 [P] [US1] Update backend/app/homework/application/get_homework_detail_use_case.py, get_homeworks_paged_use_case.py, and delete_homework_use_case.py to import HomeworkRepository from homework_repository
- [X] T014 [US1] Update backend/app/homework/controller.py to import HomeworkRepository from homework_repository and verify route dependencies

**Checkpoint**: User Story 1 hoàn tất, tất cả Use Case chuyển sang sử dụng các Repository đơn nhiệm.

---

## Phase 4: User Story 2 - Tối Ưu Truy Vấn Lọc Bài Tập Bằng SQL JOIN Trực Tiếp (Priority: P2)

**Goal**: Thay thế 100% in-memory filtering `get_all(skip=0, limit=1000)` bằng SQL JOIN trực tiếp tại database với `HomeworkAssigneeModel`.

**Independent Test**: Endpoint `GET /api/v1/homeworks/me` và `GET /api/v1/homeworks/report/unsubmitted/{user_id}` phân trang và lọc trực tiếp qua SQL JOIN, không duyệt toàn bộ bài tập trên RAM.

- [X] T015 [US2] Implement get_assigned_to_user_paged and get_all_assigned_to_user methods with SQL JOIN in backend/app/homework/infrastructure/homework_repository.py
- [X] T016 [US2] Refactor backend/app/homework/application/get_user_homeworks_use_case.py to use homework_repo.get_assigned_to_user_paged and homework_submission_repo.get_user_submissions_for_homeworks
- [X] T017 [US2] Refactor backend/app/homework/application/get_unsubmitted_homeworks_for_user_use_case.py to use homework_repo.get_all_assigned_to_user and homework_submission_repo.get_user_submissions_for_homeworks
- [X] T018 [US2] Refactor backend/app/homework/application/get_unsubmitted_homework_report_use_case.py to inject HomeworkSubmissionRepository and optimize assignee lookups

**Checkpoint**: User Story 2 hoàn tất, truy vấn bài tập cá nhân được thực hiện 100% ở tầng Database qua SQL JOIN.

---

## Phase 5: User Story 3 - Cập Nhật Dishka Provider & Xóa Bỏ File Repository Gộp Cũ (Priority: P3)

**Goal**: Xóa bỏ hoàn toàn tệp `repository.py` cũ và cập nhật toàn bộ test/call sites để loại bỏ bất kỳ alias hay import lỗi thời nào (tuân thủ Nguyên tắc X của Constitution).

**Independent Test**: Xóa file `backend/app/homework/infrastructure/repository.py`, chạy toàn bộ test suite đạt 30/30 passed và 12/12 report tests passed.

- [X] T019 [US3] Delete obsolete backend/app/homework/infrastructure/repository.py
- [X] T020 [US3] Update backend/tests/api/test_homework_api.py and any other test files importing from app.homework.infrastructure.repository
- [X] T021 [US3] Verify zero references to app.homework.infrastructure.repository remain across the entire codebase

**Checkpoint**: Tệp `repository.py` cũ đã bị xóa sạch, không có alias thừa thãi.

---

## Phase 6: Polish & Verification

**Purpose**: Chạy xác minh toàn diện theo `quickstart.md`.

- [X] T022 Execute test suite backend/.venv/bin/pytest backend/tests/api/test_homework_api.py -v
- [X] T023 Execute test suite backend/.venv/bin/pytest backend/tests/api/test_report_api.py -v
- [X] T024 Validate frontend build with npm run build in frontend directory

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: Độc lập, chạy kiểm tra ban đầu.
- **Foundational (Phase 2)**: T002, T003, T004, T005 có thể thực hiện song song (các file mới khác nhau).
- **User Story 1 (Phase 3)**: Phụ thuộc vào Phase 2 (các repository mới đã sẵn sàng).
- **User Story 2 (Phase 4)**: Phụ thuộc vào Phase 3 (các use case đã inject repository mới).
- **User Story 3 (Phase 5)**: Phụ thuộc vào Phase 4 (khi toàn bộ logic đã chuyển qua các repo mới, tiến hành xóa `repository.py` cũ).
- **Polish (Phase 6)**: Chạy test và build sau khi hoàn tất US1, US2, US3.
