# Implementation Plan: Refactor Kiến Trúc Violation Domain Theo Mô Hình Event-Driven

**Branch**: `002-violation-event-driven-refactor` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-violation-event-driven-refactor/spec.md`

## Summary

Tái cấu trúc kiến trúc của domain `Violation`, `Meeting` và `Homework` sang mô hình hướng sự kiện (Event-Driven Architecture). Loại bỏ hoàn toàn sự phụ thuộc trực tiếp (Direct Dependency / Coupling) từ `Meeting` và `Homework` sang `Violation` và `PermissionRequest`. Các domain chỉ phát hiện và phát sinh Domain Events (`ParticipantAbsenceRecorded`, `ParticipantLateRecorded`, `HomeworkOverdueDetected`), trong khi domain `Violation` sẽ lắng nghe qua `EventBus`, tự động tra cứu đơn xin phép và quyết định tạo vi phạm.

---

## Technical Context

**Language/Version**: Python 3.11+ / FastAPI
**Primary Dependencies**: Dishka (Dependency Injection), SQLAlchemy 2.0, Pydantic V2, Loguru
**Storage**: PostgreSQL (SQLAlchemy models), EventBus in-memory/async
**Testing**: pytest / pytest-asyncio
**Target Platform**: Linux / macOS Docker container
**Project Type**: Web Service API (Backend Clean Architecture)
**Performance Goals**: Xử lý event bất đồng bộ, phản hồi API < 50ms, Job quét 23:59 hoàn thành < 5 giây
**Constraints**: Zero regression trên toàn bộ test suite, 0 import chéo từ Meeting/Homework sang Violation

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Trạng thái |
| :--- | :--- | :---: |
| **I. Clean Architecture & DDD Boundaries** | Phân tách ranh giới rõ ràng: Domain thuần túy ➔ Use Cases ➔ Repositories. Domain Events làm cầu nối. |  PASS |
| **II. Dependency Injection with Dishka** | Cập nhật các Dishka providers trong `meeting/providers.py`, `homework/providers.py`, `violation/providers.py`. |  PASS |
| **III. Unified UTC+7 Timezone** | Thời gian ghi nhận trong các event và violation tuân thủ UTC+7. |  PASS |
| **IV. Event-Driven Decoupling** | Luồng xử lý vi phạm chuyển hoàn toàn sang Event-Driven qua `EventBus` (`EventHandler`). |  PASS |
| **V. API Backward Compatibility** | Giữ nguyên các API endpoints và schema phản hồi `ApiResponse[T]`. |  PASS |
| **VI. Idempotency & Network Resilience** | Xử lý kiểm tra trùng lặp vi phạm khi handler nhận nhiều lần cùng 1 event. |  PASS |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-violation-event-driven-refactor/
├── spec.md                  # Feature specification
├── plan.md                  # This implementation plan
├── research.md              # Phase 0 architectural decisions
├── data-model.md            # Phase 1 event schemas and state transitions
├── contracts/
│   └── events-contract.md   # Phase 1 event contracts & invariants
├── quickstart.md            # Phase 1 verification & test guide
└── checklists/
    └── requirements.md      # Quality checklist
```

### Source Code Touched

```text
backend/app/
├── core/
│   └── events.py                                # Đăng ký Event Handlers với EventBus
├── meeting/
│   ├── domain/
│   │   └── events.py                            # Bổ sung ParticipantAbsenceRecorded, ParticipantLateRecorded
│   ├── application/
│   │   └── attendance_use_cases.py              # Refactor: bỏ CreateViolationUseCase & PermissionRepo, chỉ phát event
│   └── providers.py                             # Cập nhật Dishka provider cho Meeting
├── homework/
│   ├── application/
│   │   └── checker_use_cases.py                 # Refactor: bỏ PermissionRepo khỏi CheckOverdueHomeworkUseCase
│   └── providers.py                             # Cập nhật Dishka provider cho Homework
└── violation/
    ├── application/
    │   └── event_handlers.py                    # Nâng cấp AutomatedViolationHandler để xử lý toàn bộ logic đối soát & tạo phạt
    └── providers.py                             # Cập nhật Dishka provider cho Violation

backend/tests/
├── test_meeting_use_cases.py                    # Cập nhật mock tests cho Meeting
├── test_homework_checker.py                     # Cập nhật tests cho Homework
└── test_violation_event_handlers.py             # Bổ sung test suite cho AutomatedViolationHandler
```

---

## Phase Breakdown

- **Phase 0: Research & Alignment**: Đã hoàn thành trong `research.md`.
- **Phase 1: Design & Contracts**: Đã hoàn thành trong `data-model.md`, `contracts/events-contract.md`, `quickstart.md`.
- **Phase 2: Execution via Tasks**: Sẽ được sinh tự động bởi lệnh `/speckit-tasks` bao gồm:
  1. Thêm Domain Events mới vào `meeting/domain/events.py` và `homework/domain/value_objects.py`.
  2. Nâng cấp `AutomatedViolationHandler` trong `violation/application/event_handlers.py`.
  3. Tách bỏ `CreateViolationUseCase` & `PermissionRequestRepository` khỏi `attendance_use_cases.py`.
  4. Cập nhật Dishka Providers và Event Registrations.
  5. Cập nhật và bổ sung Unit Tests.
