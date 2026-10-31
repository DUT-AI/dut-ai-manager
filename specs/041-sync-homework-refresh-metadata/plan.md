# Implementation Plan: Đồng Bộ Toàn Diện & Làm Mới Metadata Bài Tập Từ Quiz

**Branch**: `041-sync-homework-refresh-metadata` | **Date**: 2026-11-01 | **Spec**: [specs/041-sync-homework-refresh-metadata/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/041-sync-homework-refresh-metadata/spec.md)

**Input**: Feature specification từ `specs/041-sync-homework-refresh-metadata/spec.md`

---

## Summary

Quy trình đồng bộ bài tập từ Quiz (`SyncHomeworkFromQuizUseCase`) hiện tại chỉ kéo các bài đã nộp về bảng `homework_submissions`. Khi giảng viên thêm bài tập con mới hoặc cấu hình lại yêu cầu bài học (thêm game, thêm bài coding) trên Quiz nhưng chưa có ai nộp, hệ thống Manage không nhận diện được.

Kế hoạch này nâng cấp `SyncHomeworkFromQuizUseCase`:
1. Gọi `quiz_api.get_lesson_metadata(slug)` và `quiz_api.get_lesson_exercises(slug)` ở đầu quy trình.
2. Tự động đồng bộ và lưu cập nhật các cờ `requires_coding`, `requires_game` vào `HomeworkModel` trong database.
3. Kéo toàn bộ danh mục bài tập con mới nhất và bài nộp theo phạm vi yêu cầu mới nhất.
4. Trả về phản hồi chi tiết bao gồm tổng số bài tập con trên Quiz, số bài nộp mới và số bài nộp cập nhật.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Dishka DI, SQLAlchemy 2.0, Pydantic V2, httpx  
**Storage**: PostgreSQL (hoặc SQLite in-memory cho Unit Testing), bảng `homeworks`, `homework_assignees`, `homework_submissions`  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Docker / Linux backend container  
**Project Type**: Web Service API  
**Performance Goals**: Quá trình làm mới metadata và đồng bộ hoàn tất trong vòng < 1.5 giây đối với mỗi bài tập  
**Constraints**: 
- Graceful Degradation: Nếu Quiz API bị gián đoạn khi lấy metadata, ghi warning và fallback tiếp tục đồng bộ bài nộp mà không gây lỗi 500.
- Tuân thủ Hiến pháp DUT AI Manager v1.9.0 (No Fake Optionals, Strict Parameter Contracts, Single-Responsibility Use Case).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | ✅ PASSED | `SyncHomeworkFromQuizUseCase` nằm ở tầng application, điều phối `HomeworkRepository`, `HomeworkSubmissionRepository` và `QuizApiClient`. |
| **II. Dependency Injection with Dishka** | ✅ PASSED | Use case nhận các dependency qua constructor, được đăng ký tại `backend/app/homework/providers.py`. |
| **III. Enterprise UTC Storage** | ✅ PASSED | Tất cả timestamp nộp bài (`submitted_at`, `completed_at`) được parse qua `parse_datetime_to_utc`. |
| **VII. Strict Single-Responsibility Use Case** | ✅ PASSED | `SyncHomeworkFromQuizUseCase` có đúng một phương thức `execute(homework_id)`. |
| **X. Zero Redundant Backward Compatibility** | ✅ PASSED | Không tạo alias, không duy trì cột thừa. |
| **XIV. No Fake Optionals & Fail-Fast Parameter Contracts** | ✅ PASSED | Mọi dependency trong constructor đều non-null, không có fake `Type | None = None`. |

---

## Project Structure

### Documentation (this feature)

```text
specs/041-sync-homework-refresh-metadata/
├── spec.md              # Đặc tả yêu cầu nghiệp vụ
├── plan.md              # Kế hoạch thực thi (tài liệu này)
├── research.md          # Quyết định kỹ thuật & phân tích phương án
├── data-model.md        # Cấu trúc thực thể và DTO
├── quickstart.md        # Kịch bản kiểm thử nhanh
└── contracts/
    └── sync-homework-api.md # Hợp đồng API
```

### Source Code Impact

```text
backend/
├── app/
│   └── homework/
│       └── application/
│           └── sync_homework_use_case.py  # Nâng cấp logic đồng bộ metadata và exercises
└── tests/
    └── integration/
        └── test_homework_quiz_integration.py # Bổ sung test cases kiểm thử làm mới metadata
```

---

## Planned Phases

- **Phase 0: Research & Technical Consensus** -> Đã hoàn thành trong `research.md`.
- **Phase 1: Design & Contracts** -> Đã hoàn thành trong `data-model.md`, `quickstart.md`, `contracts/`.
- **Phase 2: Task Breakdown** -> Chạy `/speckit-tasks` để phân rã checklist hành động chi tiết.
