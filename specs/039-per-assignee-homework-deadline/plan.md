# Implementation Plan: Chuyển hoàn toàn trường Deadline của Homework sang bảng Assignees & Tích hợp đơn xin hoãn (039-per-assignee-homework-deadline)

**Branch**: `039-per-assignee-homework-deadline` | **Date**: 2026-10-31 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/039-per-assignee-homework-deadline/spec.md)

**Input**: Feature specification from `specs/039-per-assignee-homework-deadline/spec.md`

## Summary

Xoá bỏ hoàn toàn trường `deadline` trên bảng `homeworks` và dời hẳn sang bảng `homework_assignees` theo nguyên tắc Constitution Rule X (Zero Redundant Columns). Mỗi học viên khi được giao bài tập sẽ có một mốc `deadline` riêng trong bản ghi phân công. Khi học viên tạo đơn xin hoãn (`POSTPONE`), hệ thống tự động cập nhật trường `deadline` của học viên đó trong `homework_assignees` (và lưu `old_deadline` trong payload để hoàn nguyên khi xoá đơn). Job quét vi phạm `CheckOverdueHomeworkUseCase` quét độc lập theo `homework_assignees.deadline` (mặc định lùi 2 ngày), giải quyết triệt để vấn đề lọt vi phạm sau khi hết hạn hoãn.

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript / React 19 (Frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Dishka DI, Pydantic V2  
**Storage**: PostgreSQL (`homework_assignees`, `homeworks`, `permission_requests`, `homework_submissions`)  
**Testing**: `pytest` với `pytest-asyncio`  
**Target Platform**: Linux / macOS Docker container  
**Project Type**: Web Service API (Backend Clean Architecture) + React SPA Frontend  
**Performance Goals**: Quét vi phạm theo batch chỉ mục `ix_homework_assignees_deadline` < 100ms  
**Constraints**: 
- Bảo toàn múi giờ UTC (`DateTime(timezone=True)`).
- Migration an toàn: Backfill dữ liệu từ `homeworks.deadline` sang `homework_assignees.deadline` trước khi `DROP COLUMN` trên bảng `homeworks`.
- Tuân thủ Constitution Rule X: Không duy trì cột `deadline` thừa trên `homeworks`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Clean Architecture & Practical DDD Boundaries**: Tách biệt rõ Model, Repository, Entity, Use Case và EventBus.
- [x] **II. Dependency Injection with Dishka**: Mọi Use Case và Strategy mới đều được đăng ký qua Dishka provider.
- [x] **III. Enterprise UTC Storage**: Cột `deadline` mới trong `homework_assignees` lưu chuẩn `TIMESTAMPTZ` (UTC).
- [x] **IV. Event-Driven Decoupling**: Khi phát hiện quá hạn, tiếp tục phát `HomeworkOverdueDetected` lên `EventBus`.
- [x] **VII. Strict Single-Responsibility Use Cases**: Giữ nguyên nguyên tắc 1 file - 1 public execute method.
- [x] **X. Zero Redundant Backward Compatibility**: Xoá hẳn cột `deadline` cũ trên `homeworks`, dời hoàn toàn sang `homework_assignees` sau khi migration backfill.

## Project Structure

### Documentation (this feature)

```text
specs/039-per-assignee-homework-deadline/
├── spec.md              # Đặc tả yêu cầu & 5 User Stories
├── plan.md              # Kế hoạch triển khai kiến trúc
├── research.md          # Phân tích kỹ thuật & Quyết định dứt khoát bỏ homework.deadline
├── data-model.md        # Chi tiết schema migration, index và entities
├── contracts/           # Contracts & Use Case Signatures
│   └── job-contracts.md
├── quickstart.md        # Kịch bản kiểm thử nghiệm thu 6 kịch bản
└── tasks.md             # Sẽ được sinh qua /speckit-tasks
```

### Source Code Impact

```text
backend/app/
├── homework/
│   ├── domain/
│   │   ├── entity.py                        # Xóa deadline ở Homework; thêm deadline vào HomeworkAssignee
│   │   └── value_objects.py                 # Thêm DueHomeworkAssignment
│   ├── infrastructure/
│   │   ├── model.py                         # Xóa deadline ở HomeworkModel; thêm deadline vào HomeworkAssigneeModel
│   │   ├── homework_assignee_repository.py  # Thêm update_deadline, get_user_deadline, get_by_deadline_date
│   │   └── homework_repository.py           # Bỏ lọc deadline theo homeworks
│   └── application/
│       ├── check_overdue_homework_use_case.py # Quét theo homework_assignee_repo.get_by_deadline_date
│       ├── create_homework_use_case.py        # Lưu deadline vào assignees khi tạo
│       ├── update_homework_use_case.py        # Lưu deadline khi cập nhật assignees
│       ├── get_user_homeworks_use_case.py     # Lấy deadline từ assignee
│       └── get_homework_detail_use_case.py    # Lấy deadline từ assignee
├── permission_request/
│   ├── domain/
│   │   └── payloads.py                      # Thêm old_deadline vào PostponePayload
│   ├── application/
│   │   └── strategies/
│   │       └── postpone_strategy.py         # on_created cập nhật assignee.deadline, on_deleted hoàn nguyên
│   └── providers.py                         # Inject homework_assignee_repo vào PostponeStrategy
└── reminder/
    └── application/
        └── scanners/
            └── homework_scanner.py          # Quét reminder theo deadline của assignee
```

## Migration & Execution Strategy

1. **Phase 1: Database Migration (Zero-Downtime Data Migration)**
   - Viết migration Alembic/SQL:
     - Tạo cột `deadline` trên `homework_assignees`.
     - Backfill dữ liệu từ `homeworks.deadline`.
     - Đồng bộ các đơn `POSTPONE` đang hiệu lực.
     - `DROP COLUMN deadline` khỏi `homeworks`.

2. **Phase 2: Entity & Repository Refactor**
   - Cập nhật `HomeworkModel`, `HomeworkAssigneeModel`.
   - Cập nhật `Homework` entity, `HomeworkAssignee` entity.
   - Bổ sung các methods trong `HomeworkAssigneeRepository`.

3. **Phase 3: Postpone Strategy Integration**
   - Thêm `old_deadline` vào `PostponePayload`.
   - Cập nhật `PostponeStrategy` (`validate`, `on_created`, `on_deleted`).

4. **Phase 4: Use Cases & Checker Job Refactor**
   - `CreateHomeworkUseCase`, `UpdateHomeworkUseCase`.
   - `CheckOverdueHomeworkUseCase` quét theo `homework_assignees.deadline`.
   - `GetMyHomeworksUseCase` trả về deadline của assignee.

5. **Phase 5: Automated Testing & Verification**
   - Cập nhật và chạy toàn bộ unit tests, integration tests.
