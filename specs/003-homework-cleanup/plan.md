# Implementation Plan: Tối Ưu Và Dọn Dẹp Domain Homework

**Branch**: `003-homework-cleanup` | **Date**: 2026-09-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-homework-cleanup/spec.md`

## Summary

Dọn dẹp và tối ưu hóa domain Homework:
1. Tạo migration Alembic để drop bảng `homework_teams`, xóa model `HomeworkTeamModel` và quan hệ `teams` trong `HomeworkModel`.
2. Xóa bỏ hoàn toàn các class domain entity, DTO và enum legacy `HomeworkSubmission` không còn sử dụng.
3. Chuyển đổi toàn bộ logic phân công bài tập sang lưu trữ trực tiếp mảng `assignee_ids` trong bảng `homework_assignees` (UI tự phân giải team thành user IDs).
4. Gỡ bỏ phụ thuộc vào `TeamRepository` trong `CheckOverdueHomeworkUseCase` và DI container của Homework.
5. Tách các Use Case của domain Homework thành các file đơn lập (Single Responsibility) và re-export qua `app/homework/application/__init__.py`.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Dishka (DI), Pydantic V2, Alembic  
**Storage**: PostgreSQL  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Linux Server / Docker  
**Project Type**: Web Service / REST API Backend  
**Performance Goals**: Quét bài tập quá hạn dưới 2s, kiểm tra nộp bài realtime qua Quiz API nhanh chóng  
**Constraints**: Zero regression, 100% test pass, 0 typecheck diagnostics (`ty`)  
**Scale/Scope**: ~10 file code trong `app/homework`, 1 migration Alembic  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Zero Hardcoded Secrets**: Sử dụng cấu hình từ `app.core.config.settings`.
- [x] **Safe Database Migrations**: Có migration file rõ ràng (`upgrade` & `downgrade`) cho việc drop bảng `homework_teams`.
- [x] **Single Responsibility**: Tách mỗi Use Case thành 1 file độc lập.
- [x] **Type Safety**: Đảm bảo type annotations chuẩn và vượt qua `make typecheck`.
- [x] **Testing Master**: Cập nhật toàn bộ test suite cho domain Homework.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-homework-cleanup/
├── spec.md              # Feature specification
├── checklists/
│   └── requirements.md  # Quality checklist
├── plan.md              # Implementation plan (this file)
├── research.md          # Technical decisions & rationale
├── data-model.md        # Database schema & entities
├── quickstart.md        # Verification and testing guide
├── contracts/
│   └── homework_api.md  # API DTO & endpoint contracts
└── tasks.md             # Implementation tasks (/speckit-tasks output)
```

### Source Code Impacted

```text
backend/
├── alembic/versions/
│   └── xxxx_drop_homework_teams_table.py
├── app/
│   ├── core/
│   │   └── permissions.py                          # Xóa HomeworkSubmissionPermission
│   ├── rbac/
│   │   └── domain/value_objects.py                 # Xóa HomeworkSubmissionPermission
│   ├── scripts/
│   │   └── seed_permissions.py                     # Dọn dẹp permission legacy
│   └── homework/
│       ├── domain/
│       │   └── entity.py                           # Xóa HomeworkSubmission, xóa team_ids/submissions
│       ├── infrastructure/
│       │   ├── model.py                            # Xóa HomeworkTeamModel, bỏ teams
│       │   └── repository.py                       # Bỏ logic sync_teams, dùng assignees
│       ├── application/
│       │   ├── dtos.py                             # Xóa legacy submission DTOs, bỏ team_ids
│       │   ├── create_homework_use_case.py         # File đơn lập mới
│       │   ├── get_homeworks_use_case.py           # File đơn lập mới
│       │   ├── update_homework_use_case.py         # File đơn lập mới
│       │   ├── delete_homework_use_case.py         # File đơn lập mới
│       │   ├── get_homework_submission_status_use_case.py # File đơn lập mới
│       │   ├── check_overdue_homework_use_case.py  # File đơn lập mới
│       │   ├── rescan_all_homeworks_use_case.py    # File đơn lập mới
│       │   └── __init__.py                         # Re-export các use case
│       ├── controller.py                           # Cập nhật controller
│       └── providers.py                            # Gỡ TeamRepository khỏi homework DI
└── tests/
    └── test_homework/                              # Cập nhật test suite
```

---

## Complexity Tracking

| Violation / Complexity | Why Needed | Simpler Alternative Rejected Because |
|------------------------|------------|-------------------------------------|
| Drop Table Migration | Bảng `homework_teams` không còn sử dụng | Giữ bảng tạo ra dead data và gây nhầm lẫn |
| Tách 7 file Use Case | Clean Architecture & SRP | Để chung 1 file lớn vi phạm SRP và khó unit test |
