# Feature Specification: Homework Constitution Hardening

## Background & Motivation
Sau khi hoàn thành việc chuẩn hóa cơ chế đánh giá bài tập theo Single Source of Truth (SSOT) và ban hành Nguyên tắc XIX trong Hiến pháp Hệ thống (`.specify/memory/constitution.md`), module `backend/app/homework/` vẫn còn một số điểm nợ kỹ thuật vi phạm các nguyên tắc cốt lõi của Hiến pháp:
1. **Vi phạm Nguyên tắc XIII & XVII (Strict Static Typing & Elimination of Raw Dictionaries)**:
   - `HomeworkSubmissionWebhookIn.details` vẫn đang định kiểu là `dict[str, Any]` thay vì Value Object `CodingSubmissionDetails | GameSubmissionDetails`.
   - Các tham số trong `GetHomeworkSubmissionStatusUseCase._evaluate_student` (`db_exercise_map`, `db_coding_general_map`, `db_game_map`) và `HomeworkExerciseResolver._extract_coding_exercises` vẫn dùng `Any`.
2. **Vi phạm Nguyên tắc XIV (No Fake Optionals & Strict Contracts & Duck-Typing Removal)**:
   - `GetUserHomeworkSubmissionsUseCase` và `parse_typed_details` dùng `getattr(s, ...)` trên Domain Entities thay vì truy xuất thuộc tính trực tiếp theo contract của `HomeworkSubmissionEntity`.
3. **Vi phạm Nguyên tắc V & XVI (Single Source of Truth API Contracts & Non-Null Contracts)**:
   - Webhook submission endpoint (`/homeworks/webhook/submission`) và Use Case `RecordHomeworkSubmissionUseCase` trả về raw `dict[str, Any]` thay vì một Pydantic Response DTO chuẩn hóa (`HomeworkWebhookResponse`), gây đứt gãy việc sinh kiểu tự động cho API client.
4. **Lỗi Linter C901 (Cyclomatic Complexity)**:
   - `UpdateHomeworkUseCase.execute` có độ phức tạp quá cao (11 > 10), cần tách nhỏ các helper methods (`_validate_with_quiz`, `_sync_assignees_and_deadlines`).

## User Stories & Functional Requirements

### User Story 1: Strict Static Typing for Submission Details & Webhook (Backend)
- **As a** Backend Engineer & API Consumer,
- **I want** Webhook payload and submission DTOs to enforce strict types (`CodingSubmissionDetails | GameSubmissionDetails`),
- **So that** raw `dict[str, Any]` is completely eradicated from application interfaces, preventing runtime type bugs and schema drift.

#### Acceptance Criteria
- [ ] `HomeworkSubmissionWebhookIn.details` chấp nhận `CodingSubmissionDetails | GameSubmissionDetails | None`.
- [ ] Tạo mới DTO `HomeworkWebhookResponse(status: str, message: str | None = None, submission_id: int | None = None)`.
- [ ] Endpoint `/homeworks/webhook/submission` và `RecordHomeworkSubmissionUseCase.execute` trả về `ApiResponse[HomeworkWebhookResponse]`.
- [ ] Các tham số `db_exercise_map`, `db_coding_general_map`, `db_game_map` trong `GetHomeworkSubmissionStatusUseCase` và `submissions` trong `HomeworkExerciseResolver._extract_coding_exercises` được gán kiểu chính xác là `HomeworkSubmission` / `CodingHomeworkSubmission` / `GameHomeworkSubmission` (loại bỏ 100% `Any`).

### User Story 2: Remove Duck-Typing (`getattr`) on Domain Entities
- **As a** Core System Architect,
- **I want** Domain Entities in `application/` to be accessed strictly via their declared contract fields,
- **So that** defensive duck-typing (`getattr(s, "exercise_id", None)`) is removed, adhering to Principle XIV.

#### Acceptance Criteria
- [ ] `GetUserHomeworkSubmissionsUseCase` truy cập trực tiếp `s.exercise_id`, `s.exercise_title`, `s.score`, `s.attempt_number`, `s.created_at`.
- [ ] Loại bỏ duck-typing rườm rà trong `submission_dtos.py::parse_typed_details`.

### User Story 3: Refactor Codebase to Reduce Complexity (C901)
- **As a** Developer maintaining the codebase,
- **I want** all functions and methods in `backend/app/homework` to have cyclomatic complexity <= 10,
- **So that** Ruff linter passes cleanly without warnings or overrides.

#### Acceptance Criteria
- [ ] Tách `UpdateHomeworkUseCase.execute` thành các private helper methods (`_validate_with_quiz`, `_sync_assignees_and_deadlines`).
- [ ] Tách `HomeworkAssigneeRepository.sync_assignees` thành các helper methods (`_resolve_clean_deadline`, `_sync_single_assignee`).
- [ ] `backend/.venv/bin/ruff check backend/app/homework` đạt 0 lỗi (clean 100%).
- [ ] Toàn bộ 281 unit tests và 9 integration tests tiếp tục PASS 100%.
