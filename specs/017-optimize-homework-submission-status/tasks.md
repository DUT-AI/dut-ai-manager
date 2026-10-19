# Tasks: Tối Ưu Hóa Tốc Độ Tải Danh Sách Bài Nộp Chi Tiết Bài Tập (DB-First Submission Status)

**Input**: Design documents from `specs/017-optimize-homework-submission-status/`
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/submission-status.json`

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)

---

## Phase 1: Setup & Data Access (Foundational)

**Purpose**: Bổ sung hàm truy vấn tối ưu tại tầng Repository để phục vụ DB-First và loại bỏ quét toàn bộ User.

- [x] T001 [P] Thêm phương thức `get_assignees_with_user_info(homework_id)` vào `backend/app/homework/infrastructure/homework_repository.py` bằng câu lệnh SQL JOIN trực tiếp giữa `HomeworkAssigneeModel` và `UserModel`.
- [x] T002 [P] Bổ sung DTO / NamedTuple `AssigneeUserInfo` chứa `(user_id, name, avatar_url)` tại `backend/app/homework/infrastructure/homework_repository.py` hoặc `domain/entity.py`.

---

## Phase 2: User Story 1 - Tải Chi Tiết Bài Nộp Tức Thì (Priority: P1) 🎯 MVP

**Goal**: Đảm bảo endpoint `GET /api/v1/homeworks/{id}/submission-status` phản hồi dưới 100ms bằng cách loại bỏ quét User toàn hệ thống và loại bỏ gọi runtime sang Quiz API.

**Independent Test**:
- Chạy request `GET /api/v1/homeworks/72/submission-status`.
- Kết quả phản hồi < 100ms, không có log gọi mạng ra Quiz API, danh sách bài nộp và thống kê bài tập con hiển thị đầy đủ và chính xác.

### Implementation for User Story 1

- [x] T003 [US1] Cập nhật `GetHomeworkSubmissionStatusUseCase` tại `backend/app/homework/application/get_homework_submission_status_use_case.py` để sử dụng `homework_repo.get_assignees_with_user_info(homework.id)` thay vì `user_repo.get_active_users()`.
- [x] T004 [US1] Xây dựng logic trích xuất danh sách bài tập con (`ExerciseSummaryDTO`) trực tiếp từ `db_submissions` (`homework_submission_repo.get_submissions_by_homework`) trong `backend/app/homework/application/get_homework_submission_status_use_case.py` mà không phụ thuộc vào `QuizSubmissionHelper.get_lesson_exercises`.
- [x] T005 [US1] Loại bỏ các cuộc gọi runtime `get_coding_completed_map` và `get_game_completed_map` sang Quiz API trong luồng đọc của `GetHomeworkSubmissionStatusUseCase`, chuyển toàn bộ logic xác định hoàn thành Coding/Game sang đọc các bản ghi trong `db_submissions`.
- [x] T006 [US1] Đảm bảo cấu trúc DTO trả về `HomeworkSubmissionStatusResponse` tại `backend/app/homework/application/dtos.py` khớp 100% với hợp đồng API hiện tại.

---

## Phase 3: User Story 2 - Quản Trị Chủ Động Đồng Bộ Dữ Liệu Khi Cần (Priority: P2)

**Goal**: Đảm bảo chức năng đồng bộ thủ công (`POST /api/v1/homeworks/{id}/sync`) hoạt động tối ưu, chỉ đồng bộ loại bài tập được yêu cầu và chạy song song.

**Independent Test**:
- Gọi `POST /api/v1/homeworks/72/sync`.
- Hệ thống chỉ gọi API Coding (không gọi Game vì `requires_game=False`), ghi nhận bài nộp mới và cập nhật tức thì vào bảng `homework_submissions`.

### Implementation for User Story 2

- [x] T007 [US2] Tối ưu `SyncHomeworkFromQuizUseCase` tại `backend/app/homework/application/sync_homework_use_case.py` để kiểm tra cờ `homework.requires_coding` và `homework.requires_game`, bỏ qua hoàn toàn việc gọi API Game nếu `requires_game=False`.
- [x] T008 [US2] Sử dụng `asyncio.gather` để đồng bộ song song nếu bài tập vừa yêu cầu Coding vừa yêu cầu Game trong `backend/app/homework/application/sync_homework_use_case.py`.

---

## Phase 4: Polish & Kiểm Thử Toàn Diện (Verification)

**Purpose**: Đảm bảo không phát sinh regression lỗi và kiểm chứng benchmark hiệu năng.

- [x] T009 Chạy toàn bộ test suites của module homework: `pytest tests/api/test_homework_api.py -v`.
- [x] T010 Đo lường thời gian phản hồi thực tế của `GET /api/v1/homeworks/72/submission-status` để xác nhận thời gian phản hồi giảm từ > 10s xuống < 100ms.
- [x] T011 Cập nhật checklist kiểm tra chất lượng tại `specs/017-optimize-homework-submission-status/checklists/requirements.md`.
