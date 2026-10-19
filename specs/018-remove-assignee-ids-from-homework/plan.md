# Implementation Plan: Loại Bỏ `assignee_ids` Khỏi Entity `Homework`

**Branch**: `018-remove-assignee-ids-from-homework` | **Date**: 2026-10-19 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/018-remove-assignee-ids-from-homework/spec.md)

## Summary
Loại bỏ trường `assignee_ids` khỏi Domain Entity `Homework` nhằm tuân thủ nguyên tắc Aggregate Root trong Clean Architecture / DDD. Tách biệt hoàn toàn việc quản lý đề bài tập và phân công học sinh thông qua `HomeworkAssigneeRepository`.

## Technical Context
- **Language/Version**: Python 3.12
- **Primary Dependencies**: FastAPI, Dishka (DI), SQLAlchemy 2.0, Pydantic V2
- **Storage**: PostgreSQL (`homeworks`, `homework_assignees`)
- **Testing**: pytest (`tests/api/test_homework_api.py`, `tests/unit/test_homework_*.py`, `tests/integration/`)

## Constitution Check
- **Principle I (Clean Architecture & Practical DDD Boundaries)**: PASS. Domain entity `Homework` không còn gánh vác danh sách học sinh N-N. Trách nhiệm quản lý phân công do `HomeworkAssigneeRepository` đảm nhiệm.
- **Principle II (Dependency Injection with Dishka)**: PASS. Các Use Case cần phân công đều inject `HomeworkAssigneeRepository`.
- **Principle VII (Strict Single-Responsibility Use Cases)**: PASS. Không phá vỡ cấu trúc use cases.

## Implementation Steps

### Phase 1: Domain & Infrastructure Models
1. **Domain Entity (`app/homework/domain/entity.py`)**:
   - Xóa `assignee_ids: list[int] = []` khỏi `Homework`.
2. **Infrastructure Model (`app/homework/infrastructure/model.py`)**:
   - Sửa `HomeworkModel.to_entity()` để không truyền `assignee_ids`.
3. **Homework Repository (`app/homework/infrastructure/homework_repository.py`)**:
   - Xóa `sync_assignees()` và logic insert `HomeworkAssigneeModel` khỏi `create()` & `update()`.

### Phase 2: Application Use Cases
1. **`CreateHomeworkUseCase` & `UpdateHomeworkUseCase`**:
   - Inject `HomeworkAssigneeRepository`.
   - Sử dụng `homework_assignee_repo.sync_assignees` khi có `assignee_ids`.
2. **`CheckOverdueHomeworkUseCase`**:
   - Inject `HomeworkAssigneeRepository`.
   - Lấy danh sách học sinh bằng `homework_assignee_repo.get_assigned_user_ids(homework.id)`.
3. **`GetUnsubmittedHomeworkReportUseCase` & `GetUserHomeworksUseCase`**:
   - Cập nhật logic lọc theo `HomeworkAssigneeRepository`.
4. **`RescanAllHomeworksUseCase`**:
   - Cập nhật logic đồng bộ không truyền `assignee_ids` vào `Homework`.

### Phase 3: DI Providers & Tests
1. **`app/homework/providers.py`**:
   - Cập nhật provider injection cho các Use Case đã thêm dependency `HomeworkAssigneeRepository`.
2. **Unit & Integration Tests**:
   - Cập nhật các mock và assertion trong `tests/unit/test_homework_*.py`, `tests/integration/test_homework_quiz_integration.py`, `tests/api/test_homework_api.py`.
