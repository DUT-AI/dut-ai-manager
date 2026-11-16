# Implementation Plan: Homework Constitution Hardening

**Branch**: `070-homework-constitution-hardening` | **Date**: 2026-11-16 | **Spec**: [specs/070-homework-constitution-hardening/spec.md](spec.md)

**Input**: Feature specification from `specs/070-homework-constitution-hardening/spec.md`

---

## Summary

Dự án này thực hiện dọn dẹp kỹ thuật và siết chặt các nguyên tắc Hiến pháp (`.specify/memory/constitution.md`) trong toàn bộ module `backend/app/homework/`. Cụ thể:
1. Chuẩn hóa kiểu tĩnh cho Webhook DTOs: Thay thế hoàn toàn `dict[str, Any]` trong `HomeworkSubmissionWebhookIn.details` bằng Value Object `CodingSubmissionDetails | GameSubmissionDetails | None`.
2. Chuẩn hóa API Response Webhook: Thay thế `ApiResponse[dict[str, Any]]` bằng schema định kiểu mạnh `ApiResponse[HomeworkWebhookResponse]`.
3. Loại bỏ 100% `Any` và duck-typing `getattr(...)` phòng thủ trên Domain Entities (`HomeworkSubmission`) trong các Use Cases và Resolvers (`GetUserHomeworkSubmissionsUseCase`, `GetHomeworkSubmissionStatusUseCase`, `HomeworkExerciseResolver`).
4. Tái cấu trúc phân rã các hàm có độ phức tạp cao (Ruff C901 cyclomatic complexity > 10) trong `UpdateHomeworkUseCase.execute` và `HomeworkAssigneeRepository.sync_assignees`.

---

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Dishka DI, Loguru  
**Storage**: PostgreSQL (SQLAlchemy ORM with `TypeDecorator` JSON columns)  
**Testing**: pytest, pytest-asyncio, unittest.mock  
**Target Platform**: Linux server / Container (Docker)  
**Project Type**: Web Service (Backend REST API & Webhooks)  
**Performance Goals**: Không thay đổi latency; giảm overhead parsing nhờ loại bỏ duck-typing `getattr`  
**Constraints**: Bảo đảm 100% tương thích ngược với Quiz API Webhook payload; duy trì 281/281 unit tests và 9/9 integration tests PASS; Ruff linter đạt 0 lỗi  
**Scale/Scope**: Toàn bộ module `backend/app/homework/`  

---

## Constitution Check

*GATE: Evaluated against `.specify/memory/constitution.md` (v1.14.0).*

| Nguyên tắc | Đánh giá | Trạng thái | Ghi chú |
|---|---|---|---|
| **I. Clean Architecture & Practical DDD Boundaries** | Use Cases chỉ điều phối, Domain Entities giữ nghiệp vụ lõi | **PASS** | Không vi phạm ranh giới |
| **V. API Backward Compatibility & Non-Null Contract DTOs** | Webhook response trả về `HomeworkWebhookResponse` chuẩn hoá thay vì raw dict | **PASS** | Đạt chuẩn contract |
| **XIII. Structured Generic Payload & Absolute Type Safety** | Loại bỏ hoàn toàn `dict[str, Any]` khỏi `HomeworkSubmissionWebhookIn`, cấm `getattr` | **PASS** | Chuyển sang Discriminated Union / Value Objects |
| **XIV. No Fake Optionals & Fail-Fast Parameter Contracts** | Loại bỏ duck-typing `getattr(s, ...)` trên domain entities | **PASS** | Truy cập thuộc tính trực tiếp theo contract |
| **XVI. Single Source of Truth API Contracts** | Schema phản hồi Webhook được sinh tường minh qua Pydantic DTO | **PASS** | Không dùng dynamic dictionaries |
| **XVII. Strongly-Typed Storage & Zero Raw Dictionary Columns** | Mapping chi tiết bài nộp qua Value Objects | **PASS** | Tận dụng `TypeDecorator` có sẵn |
| **XIX. Single Source of Truth & Zero Fallback Logic** | Xoá bỏ duck-typing và kiểm tra kiểu thời gian chạy thừa thãi | **PASS** | Domain Entity là nguồn chân lý duy nhất |

*Kết luận*: **100% Constitution Gates PASS**.

---

## Project Structure

### Documentation (this feature)

```text
specs/070-homework-constitution-hardening/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0 research decisions and rationales
├── data-model.md        # Phase 1 data model & DTO definitions
├── quickstart.md        # Phase 1 validation & verification guide
├── contracts/           # Phase 1 interface contracts
│   └── homework_webhook_contract.md
└── tasks.md             # Phase 2 output (to be created by /speckit-tasks)
```

### Source Code Layout

```text
backend/app/homework/
├── application/
│   ├── dtos/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   └── submission_dtos.py      # Refactor: HomeworkSubmissionWebhookIn, HomeworkWebhookResponse, parse_typed_details
│   ├── get_homework_submission_status_use_case.py  # Refactor: Remove Any from maps
│   ├── get_user_homework_submissions_use_case.py   # Refactor: Remove getattr duck-typing
│   ├── homework_exercise_resolver.py              # Refactor: Remove Any and getattr
│   ├── record_submission_use_case.py               # Refactor: Return HomeworkWebhookResponse
│   └── update_homework_use_case.py                 # Refactor: Reduce C901 complexity <= 10
├── controller.py                                   # Refactor: Webhook response_model=ApiResponse[HomeworkWebhookResponse]
└── infrastructure/
    └── homework_assignee_repository.py             # Refactor: Reduce C901 complexity <= 10
```

---

## Complexity Tracking

> Không có vi phạm Hiến pháp cần biện minh. Tất cả các thay đổi đều phục vụ mục tiêu dọn dẹp vi phạm và chuẩn hóa mã nguồn.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| *None* | N/A | N/A |

---

## Phases & Execution Outline

### Phase 0: Outline & Research (Completed)
- Xem chi tiết tại [research.md](research.md).
- Giải quyết toàn bộ các quyết định kỹ thuật:
  - Cấu trúc `HomeworkSubmissionWebhookIn.details` và cơ chế parse tự động.
  - Định nghĩa DTO `HomeworkWebhookResponse`.
  - Thay thế `Any` trong maps và collections bằng `HomeworkSubmission`.
  - Loại bỏ duck-typing `getattr(...)`.
  - Phương án phân rã hàm giảm độ phức tạp C901.

### Phase 1: Design & Contracts (Completed)
- Mô hình dữ liệu & Value Objects: [data-model.md](data-model.md).
- Giao thức tích hợp Webhook API: [contracts/homework_webhook_contract.md](contracts/homework_webhook_contract.md).
- Kịch bản kiểm thử & xác minh: [quickstart.md](quickstart.md).

### Post-Design Constitution Check
Tất cả các artifacts thiết kế trong Phase 1 đã được rà soát đối chiếu với Hiến pháp:
- Không còn bất kỳ khai báo `dict[str, Any]` nào trong các DTOs.
- Không còn bất kỳ tham số `Any` nào trong các chữ ký hàm.
- Ranh giới Clean Architecture và hợp đồng tĩnh được giữ vững.
- **Trạng thái**: **APPROVED FOR IMPLEMENTATION (Sẵn sàng tạo tasks.md qua `/speckit-tasks`)**.
