# Implementation Plan: Full In-Memory Fake Test Migration for Homework Module

**Branch**: `072-homework-inmemory-test-migration` | **Date**: 2026-11-16 | **Spec**: [specs/072-homework-inmemory-test-migration/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/072-homework-inmemory-test-migration/spec.md)

**Input**: Feature specification from `/specs/072-homework-inmemory-test-migration/spec.md`

---

## Summary

Chuyển đổi toàn diện 100% các unit test cases trong module `homework` từ việc sử dụng `unittest.mock.MagicMock` gắn chặt vào chi tiết truy vấn sang sử dụng `InMemoryHomeworkRepository`, `InMemoryHomeworkSubmissionRepository`, `InMemoryHomeworkAssigneeRepository`, `FakeQuizApiClient` và `SpyEventBus`. Xóa bỏ toàn bộ các mock repository dễ vỡ, chuyển sang kiểm thử dựa trên trạng thái (State/Behavior Testing), duy trì 100% tỷ lệ PASS trên 467 tests toàn hệ thống và đạt 0 lỗi linter Ruff.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic V2, Dishka, SQLAlchemy 2.0 (chỉ ở tầng adapter / integration)  
**Storage**: In-Memory Python dictionaries (`dict[int, Entity]`, `dict[tuple[int, int], datetime]`) trong `app.homework.infrastructure.in_memory`  
**Testing Framework**: Pytest (`pytest`, `pytest-asyncio`)  
**Target Platform**: Linux / macOS server  
**Project Type**: Web Service / Modular Monolith  
**Performance Goals**: Toàn bộ unit test suite của module homework thực thi trong < 1.5 giây  
**Constraints**: Zero Mock cho Database Repositories; Tuân thủ tuyệt đối 19 nguyên tắc Hiến pháp; Không hồi quy 467 backend tests  
**Scale/Scope**: 5 file test unit trong `backend/tests/unit/test_homework_*.py` (~1500 dòng code kiểm thử)  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Hiến pháp | Trạng thái | Đánh giá & Ràng buộc tuân thủ |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | ✅ PASS | Tách biệt tuyệt đối giữa Domain Ports và In-Memory Fakes. Unit tests chỉ tương tác qua Ports và Entities. |
| **II. Dependency Injection with Dishka** | ✅ PASS | Giữ nguyên Dishka `alias` đã cấu hình ở feature 071, không can thiệp sai lệch DI. |
| **III. Enterprise UTC Storage & Vietnam Display** | ✅ PASS | Mọi datetime trong In-Memory fixtures và test assertions đều là UTC aware (`ZoneInfo("Asia/Ho_Chi_Minh")` khi cần so sánh local date). |
| **IV. Event-Driven Decoupling** | ✅ PASS | Sử dụng `SpyEventBus` để bắt và kiểm tra Domain Events (`HomeworkOverdueDetected`) mà không có side-effects. |
| **V. API Backward Compatibility** | ✅ PASS | Không thay đổi API hay DTO schema của controller. |
| **VI. Idempotency & Network Resilience** | ✅ PASS | Kiểm tra Idempotent upsert submission trực tiếp qua state trong `InMemoryHomeworkSubmissionRepository`. |
| **VII. Strict Single-Responsibility Use Cases** | ✅ PASS | Các Use Case giữ nguyên một method `execute()`. |
| **VIII. Frontend Component Modularity** | ⚪ N/A | Feature thuần backend testing. |
| **IX. Pure Composition Over Base Use Cases** | ✅ PASS | Không kế thừa Use Case nào. Fixtures tái sử dụng qua pytest injection. |
| **X. Zero Redundant Backward Compatibility** | ✅ PASS | Xóa bỏ sạch sẽ các mock cũ sau khi test In-Memory đã bao phủ 1:1, không giữ lại code chết. |
| **XI. Plain Text Notifications** | ✅ PASS | Nội dung thông báo trong sự kiện `HomeworkOverdueDetected` không chứa raw markdown. |
| **XII. Server-Driven Filtering** | ⚪ N/A | Không thay đổi pagination query. |
| **XIII. Structured Generic Payload & Absolute Type Safety** | ✅ PASS | Dữ liệu `details` trong bài nộp dùng `CodingSubmissionDetails` và `GameSubmissionDetails` Value Objects chuẩn type. |
| **XIV. No Fake Optionals & Fail-Fast Contracts** | ✅ PASS | Mọi dependencies truyền vào Use Case trong test là bắt buộc và non-null. |
| **XV. Unified Client Networking** | ⚪ N/A | Feature backend testing. |
| **XVI. Maximum Deadline Protection** | ✅ PASS | Bộ test kiểm tra nguyên tắc Max Deadline Rule trực tiếp qua `InMemoryHomeworkAssigneeRepository.sync_assignees`. |
| **XVII. Pure UUID V7 Entity Identifiers** | ✅ PASS | Không phá vỡ hệ thống ID hiện tại. |
| **XVIII. Strict Type Generation** | ⚪ N/A | Không sửa đổi OpenAPI endpoints. |
| **XIX. Single Source of Truth & Zero Fallback Logic** | ✅ PASS | Kiểm tra `Homework.evaluate_submissions` là SSOT duy nhất trong mọi kịch bản kiểm tra hạn. |

---

## Project Structure

### Documentation (this feature)

```text
specs/072-homework-inmemory-test-migration/
├── plan.md              # File kế hoạch này
├── research.md          # Các quyết định thiết kế fixture & migration
├── data-model.md        # Topology In-Memory State & Fixtures
├── quickstart.md        # Hướng dẫn xác minh sau khi chuyển đổi
├── contracts/
│   └── fixtures_contract.md # Hợp đồng fixtures & assertions
└── tasks.md             # Sẽ được sinh ra bởi /speckit-tasks
```

### Source Code & Test Files Layout

```text
backend/
├── app/homework/
│   ├── domain/ports/
│   │   ├── homework_repository_port.py
│   │   ├── homework_submission_repository_port.py
│   │   └── homework_assignee_repository_port.py
│   └── infrastructure/in_memory/
│       ├── in_memory_homework_repo.py
│       ├── in_memory_submission_repo.py
│       └── in_memory_assignee_repo.py
└── tests/
    ├── fixtures/
    │   └── homework_fixtures.py     # Shared fixtures (in_memory repos, fake quiz, spy bus)
    └── unit/
        ├── test_homework_checker.py          # Refactored: 100% In-Memory (Zero Mock)
        ├── test_homework_scanner.py          # Refactored: 100% In-Memory (Zero Mock)
        ├── test_homework_validation.py       # Refactored: 100% In-Memory (Zero Mock)
        ├── test_homework_ssot.py             # Refactored: 100% In-Memory (Zero Mock)
        ├── test_homework_max_deadline_rule.py# Refactored: 100% In-Memory (Zero Mock)
        ├── test_homework_pure_domain.py      # Giữ nguyên: Pure domain
        ├── test_homework_ports_contract.py   # Giữ nguyên: Contract verification
        └── test_homework_in_memory_use_cases.py # Giữ nguyên: End-to-end in-memory flows
```

---

## Phase 0: Outline & Research

Đã hoàn thành tại [`research.md`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/072-homework-inmemory-test-migration/research.md) với 4 quyết định kỹ thuật:
1. Tạo module shared fixture tập trung `backend/tests/fixtures/homework_fixtures.py`.
2. Refactor trực tiếp các file test unit hiện tại để bảo toàn tên hàm, kịch bản, và lịch sử git.
3. Chuyển đổi kiểm thử từ `assert_called_once_with` sang kiểm tra trạng thái thực tế trong RAM.
4. Giữ `FakeQuizApiClient` và `SpyEventBus` làm Test Doubles chuẩn cho các ranh giới ngoại vi.

---

## Phase 1: Design & Contracts

Đã hoàn thành các artifacts thiết kế:
- [`data-model.md`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/072-homework-inmemory-test-migration/data-model.md): Topology In-Memory State & Data Seeding conventions.
- [`contracts/fixtures_contract.md`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/072-homework-inmemory-test-migration/contracts/fixtures_contract.md): Hợp đồng fixtures và assertions kiểm tra trạng thái.
- [`quickstart.md`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/072-homework-inmemory-test-migration/quickstart.md): 4 kịch bản xác minh Zero-Mock và regression testing.

---

## Post-Design Constitution Check

Toàn bộ 19 nguyên tắc Hiến pháp tiếp tục **100% PASS** sau khi hoàn tất thiết kế Phase 1. Sẵn sàng cho bước lập nhiệm vụ chi tiết (`/speckit-tasks`).
