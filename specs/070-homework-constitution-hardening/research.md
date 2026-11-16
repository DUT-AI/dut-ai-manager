# Research: Homework Constitution Hardening

**Feature**: `070-homework-constitution-hardening`  
**Date**: 2026-11-16  
**Status**: Completed  

---

## 1. Research Objectives
Nghiên cứu và chuẩn hóa các giải pháp loại bỏ triệt để 4 vi phạm Hiến pháp (`.specify/memory/constitution.md`) trong module `backend/app/homework`:
1. Vi phạm Nguyên tắc XIII & XVII: Sử dụng `dict[str, Any]` trong Webhook DTOs và `Any` trong maps/collections.
2. Vi phạm Nguyên tắc XIV & XIX: Sử dụng `getattr(...)` duck-typing phòng thủ trên Domain Entities (`HomeworkSubmission`).
3. Vi phạm Nguyên tắc V & XVI: Trả về `dict[str, Any]` tại endpoint `/homeworks/webhook/submission` và Use Case `RecordHomeworkSubmissionUseCase`.
4. Lỗi linter C901 (Cyclomatic Complexity > 10): Trong `UpdateHomeworkUseCase.execute` và `HomeworkAssigneeRepository.sync_assignees`.

---

## 2. Decisions, Rationales & Alternatives

### Decision 1: Strongly-Typed Webhook DTOs (`details: CodingSubmissionDetails | GameSubmissionDetails | None`)
- **Decision**: 
  - Đổi kiểu trường `details` trong `HomeworkSubmissionWebhookIn` từ `dict[str, Any]` sang `CodingSubmissionDetails | GameSubmissionDetails | None = None`.
  - Bổ sung `model_validator(mode="before")` để tự động parse raw dictionary payload từ Quiz Webhook thành đúng Pydantic Value Object (`CodingSubmissionDetails` nếu `type == "CODING"`, `GameSubmissionDetails` nếu `type == "GAME"`).
- **Rationale**:
  - Tuân thủ nghiêm ngặt **Nguyên tắc XIII (Structured Generic Payload & Absolute Type Safety)** và **Nguyên tắc XVII (Strongly-Typed Storage & Zero Raw Dictionary Columns)**.
  - Ngăn ngừa runtime schema drift, đảm bảo OpenAPI spec hiển thị rõ cấu trúc chi tiết của bài nộp.
- **Alternatives Considered**:
  - *Giữ nguyên `dict[str, Any]`*: Bị bác bỏ vì vi phạm Hiến pháp, không đảm bảo an toàn kiểu dữ liệu tĩnh.
  - *Tạo 2 schema webhook riêng biệt (`CodingWebhookIn`, `GameWebhookIn`)*: Bị bác bỏ vì hệ thống Quiz API hiện tại chỉ gửi về một endpoint duy nhất với trường `type: "CODING" | "GAME"`. Sử dụng Union + Discriminator validator phù hợp hơn với hiện trạng tích hợp.

---

### Decision 2: Elimination of `Any` in Maps and Submission Collections
- **Decision**:
  - Tại `GetHomeworkSubmissionStatusUseCase._evaluate_student`:
    - `db_exercise_map: dict[tuple[int, str], HomeworkSubmission]`
    - `db_coding_general_map: dict[int, HomeworkSubmission]`
    - `db_game_map: dict[int, HomeworkSubmission]`
  - Tại `HomeworkExerciseResolver._extract_coding_exercises`:
    - Đổi chữ ký từ `submissions: list[Any]` sang `submissions: list[HomeworkSubmission]`.
    - Thay thế toàn bộ `getattr(sub, ...)` bằng truy cập thuộc tính trực tiếp: `sub.submission_type`, `sub.exercise_id`, `sub.exercise_title`.
  - Xóa bỏ import `from typing import Any` khỏi `homework_exercise_resolver.py` và các file liên quan.
- **Rationale**:
  - `Homework.index_submissions` đã trả về kiểu `tuple[dict[tuple[int, str], HomeworkSubmission], dict[int, HomeworkSubmission], dict[int, HomeworkSubmission]]`.
  - `HomeworkSubmission` là Domain Entity có các trường thuộc tính tường minh (`submission_type`, `exercise_id`, `exercise_title`). Duck-typing `getattr` là tàn dư của mã phòng thủ cũ, vi phạm **Nguyên tắc XIV & XIX**.
- **Alternatives Considered**:
  - *Dùng `Protocol`*: Không cần thiết vì toàn bộ luồng đều chạy qua Domain Entity `HomeworkSubmission`.

---

### Decision 3: Standardized `HomeworkWebhookResponse` Pydantic DTO
- **Decision**:
  - Định nghĩa mới DTO `HomeworkWebhookResponse(BaseModel)` tại `backend/app/homework/application/dtos/submission_dtos.py`:
    ```python
    class HomeworkWebhookResponse(BaseModel):
        status: str  # "recorded" | "updated" | "ignored"
        message: str | None = None
        reason: str | None = None
        submission_id: int | None = None
        homework_id: int | None = None
        user_id: int | None = None
        exercise_id: str | None = None
    ```
  - Cập nhật kiểu trả về của `RecordHomeworkSubmissionUseCase.execute(payload) -> HomeworkWebhookResponse`.
  - Cập nhật Controller endpoint: `@router.post("/webhook/submission", response_model=ApiResponse[HomeworkWebhookResponse])`.
- **Rationale**:
  - Tuân thủ **Nguyên tắc V (API Backward Compatibility & Non-Null Contract DTOs)** và **Nguyên tắc XVI (Single Source of Truth API Contracts)**.
  - Loại bỏ hoàn toàn raw dict trả về ở presentation layer, cho phép `openapi-typescript` sinh type an toàn cho client.
- **Alternatives Considered**:
  - *Trả về boolean*: Thiếu thông tin audit trail và tracking ID cho Quiz API khi debug.

---

### Decision 4: Elimination of Duck-Typing (`getattr`) in Domain & Application Use Cases
- **Decision**:
  - Trong `GetUserHomeworkSubmissionsUseCase`:
    - Truy cập trực tiếp thuộc tính: `s.exercise_id`, `s.exercise_title`, `s.score`, `s.attempt_number or 1`, `s.created_at`.
  - Trong `HomeworkSubmissionDetailResponse.parse_typed_details`:
    - Xử lý phân biệt rõ ràng giữa input là `HomeworkSubmission` domain entity (truy cập thuộc tính trực tiếp) và input là dictionary thô.
- **Rationale**:
  - Tuân thủ **Nguyên tắc XIV (No Fake Optionals & Fail-Fast Parameter Contracts)** và **Nguyên tắc XIX (Single Source of Truth & Zero Fallback Logic)**.
  - Fail-fast ngay lập tức nếu Entity vi phạm schema thay vì âm thầm trả về `None`.
- **Alternatives Considered**:
  - *Dùng `hasattr`*: Vẫn là duck-typing, vi phạm cùng nguyên tắc.

---

### Decision 5: Refactoring for Cyclomatic Complexity <= 10 (Ruff C901)
- **Decision**:
  - Trong `UpdateHomeworkUseCase.execute`:
    - Tách logic xác thực Quiz sang `_validate_requirements(self, effective_coding: bool, effective_game: bool, extracted_slug: str) -> None`.
    - Tách logic đồng bộ assignee sang `_sync_assignees_and_deadlines(self, homework_id: int, data: HomeworkUpdate) -> None`.
    - Hạ độ phức tạp cyclomatic từ 11 xuống <= 5.
  - Trong `HomeworkAssigneeRepository.sync_assignees`:
    - Tách `_resolve_clean_deadline(...) -> datetime`.
    - Tách `_update_assignee_deadline(...)` và `_insert_new_assignees(...)`.
    - Hạ độ phức tạp cyclomatic từ 11 xuống <= 6.
- **Rationale**:
  - Đảm bảo linter Ruff kiểm tra đạt 0 lỗi mà không cần dùng `# noqa: C901`.
  - Tăng tính mô-đun và dễ bảo trì cho mã nguồn.
- **Alternatives Considered**:
  - *Dùng `# noqa: C901`*: Bị nghiêm cấm bởi quy chuẩn kỹ thuật của dự án.

---

## 3. Best Practices & Guidelines
1. **Linter Verification**: Chạy `backend/.venv/bin/ruff check backend/app/homework` sau mỗi thay đổi.
2. **Regression Testing**: Chạy `backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py` và `backend/tests/integration/test_homework_*.py` để bảo đảm 100% tests PASS.
3. **OpenAPI Sync**: Khởi chạy hoặc kiểm tra router contract đảm bảo schema hợp lệ.
