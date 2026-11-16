# Implementation Plan: System Architecture Redesign & Clean Architecture Blueprint (Homework Module Pilot)

**Branch**: `071-architecture-redesign` | **Date**: 2026-11-16 | **Spec**: [specs/071-architecture-redesign/spec.md](spec.md)

**Input**: Feature specification from `specs/071-architecture-redesign/spec.md`

---

## Summary

Dự án này triển khai khuôn mẫu kiến trúc chuẩn mực (Clean Architecture & Ports/Adapters) thí điểm trên module `backend/app/homework`, nhằm giải quyết triệt để vấn đề coupling giữa Use Cases và Database (Mocking Hell):
1. **Xây dựng Repository Ports**: Khai báo abstract interfaces thuần túy (`HomeworkRepositoryPort`, `HomeworkSubmissionRepositoryPort`, `HomeworkAssigneeRepositoryPort`) tại `backend/app/homework/domain/ports/`.
2. **Xây dựng In-Memory Fake Repositories**: Cài đặt các kho lưu trữ trên RAM (`InMemoryHomeworkRepository`, `InMemoryHomeworkSubmissionRepository`, `InMemoryHomeworkAssigneeRepository`) tại `backend/app/homework/infrastructure/in_memory/`.
3. **Refactor SQLAlchemy Repositories**: Cho các repository hiện tại kế thừa trực tiếp từ Ports để đảm bảo tính tương thích ngược 100%.
4. **Cấu hình Dishka DI**: Đăng ký bindings cho Ports trong `providers.py`, cho phép hoán đổi adapter linh hoạt.
5. **Chuyển đổi Unit Tests**: Refactor các bài test Use Case để sử dụng In-Memory Repositories, loại bỏ sự phụ thuộc vào `MagicMock` cho database queries.

---

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Dishka DI, Loguru  
**Storage**: PostgreSQL (SQLAlchemy ORM adapter) & In-Memory RAM adapter (pure Python data structures)  
**Testing**: pytest, pytest-asyncio, In-Memory Fakes (Zero DB mock)  
**Target Platform**: Linux server / Container (Docker)  
**Project Type**: Enterprise Web Service (Clean Architecture / Hexagonal Pilot)  
**Performance Goals**: Unit test suite chạy < 0.1s; latency runtime không thay đổi  
**Constraints**: 100% tương thích ngược với API Controller và DB hiện tại; 455 tests backend tiếp tục PASS 100%; linter Ruff sạch 0 lỗi  
**Scale/Scope**: Thí điểm trên module `backend/app/homework/` trước khi nhân rộng  

---

## Constitution Check

*GATE: Evaluated against `.specify/memory/constitution.md` (v1.14.0).*

| Nguyên tắc | Đánh giá | Trạng thái | Ghi chú |
|---|---|---|---|
| **I. Clean Architecture & Practical DDD Boundaries** | Ranh giới giữa Domain Ports, Use Cases, và Infrastructure Adapters được tách biệt tuyệt đối | **PASS** | Hoàn toàn độc lập |
| **II. Dependency Injection with Dishka** | Cung cấp Repository qua Port interface trong `providers.py` | **PASS** | Chuẩn hóa DI |
| **IX. Pure Composition & Domain Services** | Sử dụng Ports & In-Memory Fakes qua composition | **PASS** | Không dùng base class cồng kềnh |
| **XIII. Structured Generic Payload & Absolute Type Safety** | 100% DTOs và Value Objects định kiểu mạnh, không `dict[str, Any]` | **PASS** | Tuyệt đối an toàn kiểu |
| **XIV. No Fake Optionals & Fail-Fast Parameter Contracts** | Ports định nghĩa tham số bắt buộc, không fake optional | **PASS** | Fail-fast tại interface |
| **XVII. Strongly-Typed Storage & Zero Raw Dictionaries** | In-Memory lưu trữ trực tiếp Domain Entities | **PASS** | Không serialize thô |
| **XIX. Single Source of Truth & Zero Fallback Logic** | Domain Aggregate Root giữ toàn bộ phán đoán, In-Memory Repo phản ánh đúng dữ liệu | **PASS** | Loại bỏ test mock sai lệch |

*Kết luận*: **100% Constitution Gates PASS**.

---

## Project Structure

### Documentation (this feature)

```text
specs/071-architecture-redesign/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0 research decisions & architecture rationales
├── data-model.md        # Phase 1 ports hierarchy & in-memory structures
├── quickstart.md        # Phase 1 validation & verification guide
├── contracts/           # Phase 1 interface contracts
│   └── ports_contract.md
└── checklists/
    └── requirements.md  # Quality checklist (16/16 PASS)
```

### Source Code Layout

```text
backend/app/homework/
├── domain/
│   ├── entity.py
│   ├── value_objects.py
│   └── ports/                             # NEW: Abstract Repository Ports
│       ├── __init__.py
│       ├── homework_repository_port.py
│       ├── homework_submission_repository_port.py
│       └── homework_assignee_repository_port.py
├── infrastructure/
│   ├── homework_repository.py             # REFACTOR: Implements HomeworkRepositoryPort
│   ├── homework_submission_repository.py  # REFACTOR: Implements HomeworkSubmissionRepositoryPort
│   ├── homework_assignee_repository.py    # REFACTOR: Implements HomeworkAssigneeRepositoryPort
│   └── in_memory/                         # NEW: In-Memory Fake Repositories
│       ├── __init__.py
│       ├── in_memory_homework_repo.py
│       ├── in_memory_submission_repo.py
│       └── in_memory_assignee_repo.py
└── providers.py                           # REFACTOR: Bind Ports in Dishka

backend/tests/
└── unit/
    ├── test_homework_ports_contract.py    # NEW: Verify both adapters satisfy ports
    └── test_homework_in_memory_use_cases.py # NEW: Zero-mock use case tests
```

---

## Complexity Tracking

> Không có vi phạm Hiến pháp cần biện minh. Toàn bộ thiết kế nhằm gia cố tính độc lập và năng lực kiểm thử của hệ thống.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| *None* | N/A | N/A |

---

## Phases & Execution Outline

### Phase 0: Outline & Research (Completed)
- Xem chi tiết tại [research.md](research.md).
- Xác lập quyết định: Vị trí Ports tại `domain/ports/`, In-Memory Fakes tại `infrastructure/in_memory/`, và giữ nguyên backward compatibility cho SQLAlchemy classes.

### Phase 1: Design & Contracts (Completed)
- Mô hình phân cấp Ports & In-Memory: [data-model.md](data-model.md).
- Hợp đồng chi tiết các phương thức Ports: [contracts/ports_contract.md](contracts/ports_contract.md).
- Kịch bản kiểm thử & xác minh: [quickstart.md](quickstart.md).

### Post-Design Constitution Check
Tất cả các artifacts thiết kế trong Phase 1 đã được rà soát:
- Không còn phụ thuộc trực tiếp vào DB trong định nghĩa Ports.
- Tầng Domain không import bất kỳ package bên ngoài nào.
- **Trạng thái**: **APPROVED FOR IMPLEMENTATION (Sẵn sàng tạo tasks qua `/speckit-tasks`)**.
