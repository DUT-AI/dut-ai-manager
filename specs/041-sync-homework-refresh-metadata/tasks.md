# Tasks: Đồng Bộ Toàn Diện & Làm Mới Metadata Bài Tập Từ Quiz (Sync Homework & Refresh Quiz Metadata)

**Input**: Design documents from `specs/041-sync-homework-refresh-metadata/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/sync-homework-api.md`, `quickstart.md`).  
**Branch**: `041-sync-homework-refresh-metadata`  
**Status**: Completed  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Có thể chạy song song (các file khác nhau, không phụ thuộc).
- **[Story]**: Gắn với User Story tương ứng (`[US1]`, `[US2]`, `[US3]`).
- Đường dẫn file tuyệt đối hoặc tương đối chuẩn xác được nêu trong mô tả.

---

## Phase 1: Setup & Environment Readiness

**Purpose**: Chuẩn bị môi trường, kiểm tra branch và xác nhận các test suite hiện tại đều xanh trước khi chạm vào mã nguồn.

- [X] T001 Kiểm tra branch git hiện tại `041-sync-homework-refresh-metadata` và kiểm thử regression toàn bộ test suite liên quan đến homework
- [X] T002 Xác nhận các phương thức `get_lesson_metadata` và `get_lesson_exercises` đã có sẵn và sẵn sàng trong `backend/app/homework/infrastructure/quiz_api.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Nền tảng cấu trúc DTO và phương thức Repository cần thiết trước khi triển khai logic nghiệp vụ.

- [X] T003 Khai báo DTO kiểu dữ liệu kết quả đồng bộ `SyncHomeworkResult` (hoặc dictionary structure tương thích) trong `backend/app/homework/application/dtos.py`
- [X] T004 Kiểm tra đảm bảo phương thức `save` và `get_by_id` của `HomeworkRepository` trong `backend/app/homework/infrastructure/homework_repository.py` đã hỗ trợ cập nhật và lưu các cờ `requires_coding` và `requires_game`

**Checkpoint**: Nền tảng DTO & Repository sẵn sàng, bắt đầu triển khai các User Story.

---

## Phase 3: User Story 1 - Tự động làm mới cấu hình bài tập từ Quiz khi đồng bộ (Priority: P1) 🎯 MVP

**Goal**: Khi người dùng gọi đồng bộ qua `SyncHomeworkFromQuizUseCase`, hệ thống tự động gọi `quiz_api.get_lesson_metadata(slug)` ở đầu quy trình. Nếu Quiz có thay đổi về `has_coding` hoặc `has_game`, use case cập nhật lại cờ của entity và lưu xuống database qua `homework_repo.save()`, đồng thời kích hoạt đồng bộ tương ứng. Bọc Fail-Safe để không ngắt quãng nếu Quiz API lỗi mạng.

**Independent Test**:
- Mock `quiz_api.get_lesson_metadata` trả về `{ "has_coding": True, "has_game": True }` cho một bài tập ban đầu chỉ có `requires_game=False`.
- Gọi `SyncHomeworkFromQuizUseCase.execute(homework_id)`.
- Xác nhận entity được lưu lại với `requires_game=True` và cả hai tiến trình đồng bộ coding lẫn game đều được kích hoạt.

### Tests for User Story 1
- [X] T005 [P] [US1] Viết unit/integration test kiểm thử tự động cập nhật cờ `requires_game` và `requires_coding` từ Quiz metadata trong `backend/tests/integration/test_homework_quiz_integration.py`
- [X] T006 [P] [US1] Viết test kiểm thử Fail-Safe: khi `quiz_api.get_lesson_metadata` gặp sự cố mạng hoặc 404 thì use case vẫn tiếp tục đồng bộ bài nộp bình thường với log warning trong `backend/tests/integration/test_homework_quiz_integration.py`

### Implementation for User Story 1
- [X] T007 [US1] Bổ sung logic gọi `quiz_api.get_lesson_metadata(slug)` ở đầu hàm `SyncHomeworkFromQuizUseCase.execute()` trong `backend/app/homework/application/sync_homework_use_case.py`
- [X] T008 [US1] So sánh cờ `requires_coding` và `requires_game` hiện tại với `has_coding` và `has_game` từ Quiz; nếu có sự thay đổi thì cập nhật entity và gọi `homework_repo.save(homework)` trong `backend/app/homework/application/sync_homework_use_case.py`
- [X] T009 [US1] Đảm bảo khối quét bài nộp Coding và Game sử dụng trạng thái cờ mới nhất vừa được cập nhật trong `backend/app/homework/application/sync_homework_use_case.py`

**Checkpoint**: User Story 1 hoàn thành và vượt qua kiểm thử độc lập. Hệ thống tự động làm mới cờ cấu hình bài tập khi đồng bộ.

---

## Phase 4: User Story 2 - Nhận diện danh mục bài tập con mới dù chưa có ai nộp (Priority: P2)

**Goal**: Gọi `quiz_api.get_lesson_exercises(slug)` khi đồng bộ để nhận diện đầy đủ danh sách bài tập con mới trên Quiz, trích xuất chính xác số lượng `coding_exercises_count` và `game_questions_count`.

**Independent Test**:
- Giả lập bài học có bài tập con mới trên Quiz nhưng danh sách nộp bài rỗng.
- Gọi đồng bộ và kiểm tra kết quả trả về nhận diện đúng số lượng bài tập con hiện có từ Quiz API.

### Tests for User Story 2
- [X] T010 [P] [US2] Viết test kiểm thử nhận diện số lượng bài tập con coding và câu hỏi game khi chưa có ai nộp bài trong `backend/tests/integration/test_homework_quiz_integration.py`

### Implementation for User Story 2
- [X] T011 [US2] Tích hợp gọi `quiz_api.get_lesson_exercises(slug)` với xử lý try/except fail-safe trong `backend/app/homework/application/sync_homework_use_case.py`
- [X] T012 [US2] Thống kê tổng số lượng bài tập con coding (`coding_exercises_count`) từ metadata/exercises và số câu hỏi game (`game_questions_count`) từ metadata trong `backend/app/homework/application/sync_homework_use_case.py`

**Checkpoint**: User Stories 1 & 2 hoạt động hoàn hảo cùng nhau. Danh mục bài tập con mới được nhận diện chính xác.

---

## Phase 5: User Story 3 - Phản hồi kết quả đồng bộ chi tiết và minh bạch (Priority: P3)

**Goal**: Chuẩn hóa payload trả về của `SyncHomeworkFromQuizUseCase.execute()` và endpoint `POST /api/v1/homeworks/{homework_id}/sync` chứa đầy đủ thông tin: `requires_coding`, `requires_game`, `coding_exercises_count`, `game_questions_count`, `synced_coding_count`, `updated_coding_count`, `synced_game_count`, `updated_game_count` và `message` thân thiện.

**Independent Test**:
- Kiểm tra kết quả trả về của use case và endpoint API theo đúng hợp đồng `specs/041-sync-homework-refresh-metadata/contracts/sync-homework-api.md`.

### Tests for User Story 3
- [X] T013 [P] [US3] Viết test kiểm tra cấu trúc payload kết quả trả về của `SyncHomeworkFromQuizUseCase` đảm bảo tuân thủ hợp đồng API trong `backend/tests/integration/test_homework_quiz_integration.py`

### Implementation for User Story 3
- [X] T014 [US3] Cập nhật từ điển trả về của `SyncHomeworkFromQuizUseCase.execute()` để bao gồm đầy đủ các trường `requires_coding`, `requires_game`, `coding_exercises_count`, `game_questions_count`, và thông điệp `message` chi tiết trong `backend/app/homework/application/sync_homework_use_case.py`

**Checkpoint**: Cả 3 User Stories hoàn thành đầy đủ, đáp ứng trọn vẹn hợp đồng API và mong muốn của người dùng.

---

## Phase 6: Polish, Verification & Quality Assurance

**Purpose**: Kiểm thử toàn diện toàn bộ test suite, chạy linter, kiểm tra tuân thủ Hiến pháp DUT AI Manager v1.9.0.

- [X] T015 Chạy toàn bộ test suite `pytest backend/tests` và xác nhận 100% tests pass không có regression
- [X] T016 Chạy `ruff check backend` và `ruff format backend` để đảm bảo code sạch, chuẩn style
- [X] T017 Xác minh các kịch bản kiểm thử trong `specs/041-sync-homework-refresh-metadata/quickstart.md`
- [X] T018 Cập nhật trạng thái checklist trong `tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)** & **Phase 2 (Foundational)**: Thực thi trước tiên.
- **Phase 3 (User Story 1 - P1 MVP)**: Triển khai ngay sau Phase 2.
- **Phase 4 (User Story 2 - P2)**: Kế thừa từ User Story 1, tích hợp `get_lesson_exercises`.
- **Phase 5 (User Story 3 - P3)**: Hoàn thiện định dạng dữ liệu trả về và thông điệp.
- **Phase 6 (Polish & Verification)**: Chạy kiểm thử toàn bộ hệ thống sau khi hoàn thành cả 3 stories.

### Parallel Opportunities
- T005, T006, T010, T013 (các bài test) có thể viết song song hoặc chuẩn bị trước trong file test.
- T003 (DTO) có thể tạo độc lập với use case.
