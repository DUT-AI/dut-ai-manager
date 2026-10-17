# Implementation Plan: Tách Biệt Các Repository Trong Module Homework & Tối Ưu SQL Join Cho Assignee

**Branch**: `015-modular-homework-repositories` | **Date**: 2026-10-18 | **Spec**: [specs/015-modular-homework-repositories/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/015-modular-homework-repositories/spec.md)

**Input**: Feature specification from `specs/015-modular-homework-repositories/spec.md`

## Summary

Refactor tệp nguyên khối `backend/app/homework/infrastructure/repository.py` (405 dòng code) thành 3 repository riêng biệt theo ranh giới thực thể DDD (`HomeworkRepository`, `HomeworkSubmissionRepository`, `HomeworkAssigneeRepository`). Đồng thời thay thế hoàn toàn anti-pattern truy vấn (kéo 1000 bản ghi về RAM để lọc bài tập của user bằng Python) bằng truy vấn SQL JOIN trực tiếp với bảng `homework_assignees` ở tầng Database. Xóa bỏ hoàn toàn tệp `repository.py` cũ và cập nhật toàn bộ call sites theo đúng Constitution v1.5.0 Nguyên tắc X.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (ORM / Core Select), Dishka (IoC/DI container)
**Storage**: PostgreSQL
**Testing**: pytest (30 tests trong `test_homework_api.py`, 12 tests trong `test_report_api.py`)
**Target Platform**: Linux Server / macOS Local Development
**Project Type**: Web Service (Backend REST API)
**Performance Goals**: Truy vấn lấy bài tập cá nhân `/api/v1/homeworks/me` phân trang trực tiếp ở tầng DB, thời gian truy vấn < 50ms, bộ nhớ $O(1)$ thay vì $O(N)$.
**Constraints**: 
- Không sửa schema bảng database hay Alembic migration.
- Không tạo alias backward compatibility thừa (Constitution Nguyên tắc X).
- Đảm bảo 100% tests pass.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Constitution | Đánh giá | Ghi chú tuân thủ |
|---|---|---|
| **I. Clean Architecture & Practical DDD Boundaries** | **PASS** | Tách tầng Infrastructure thành các repository đơn nhiệm tương ứng với từng Aggregate/bảng dữ liệu. |
| **II. Dependency Injection with Dishka** | **PASS** | Đăng ký rõ ràng 3 repository mới vào `HomeworkModuleProvider` với `Scope.REQUEST`. |
| **VII. Strict Single-Responsibility Use Cases** | **PASS** | Duy trì mỗi use case 1 file, inject đúng các repository chuyên biệt phục vụ logic nghiệp vụ. |
| **IX. Pure Composition Over Base Use Cases** | **PASS** | Các use case sử dụng pure composition, inject độc lập `HomeworkRepository`, `HomeworkSubmissionRepository`, hoặc `HomeworkAssigneeRepository`. |
| **X. Zero Redundant Backward Compatibility** | **PASS** | Xóa bỏ hoàn toàn file cũ `repository.py`, cập nhật 100% call site sang file repository mới, không tạo alias giả mạo. |

## Project Structure

### Documentation (this feature)

```text
specs/015-modular-homework-repositories/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code Layout

```text
backend/app/homework/
├── infrastructure/
│   ├── __init__.py                          # Re-export 3 canonical repositories
│   ├── homework_repository.py               # Repository quản lý HomeworkModel & SQL JOIN
│   ├── homework_submission_repository.py    # Repository quản lý HomeworkSubmissionModel
│   ├── homework_assignee_repository.py      # Repository quản lý HomeworkAssigneeModel
│   ├── model.py                             # ORM models (giữ nguyên)
│   └── quiz_api.py                          # Quiz Client (giữ nguyên)
├── application/
│   ├── get_user_homeworks_use_case.py       # Sử dụng SQL JOIN paged thay vì in-memory filter
│   ├── get_unsubmitted_homeworks_for_user_use_case.py # Sử dụng SQL JOIN trực tiếp
│   ├── get_unsubmitted_homework_report_use_case.py    # Inject HomeworkRepository + HomeworkSubmissionRepository
│   ├── create_homework_use_case.py          # Inject HomeworkRepository + HomeworkAssigneeRepository
│   ├── update_homework_use_case.py          # Inject HomeworkRepository + HomeworkAssigneeRepository
│   ├── sync_homework_use_case.py            # Inject HomeworkRepository + HomeworkSubmissionRepository
│   ├── record_submission_use_case.py        # Inject HomeworkRepository + HomeworkSubmissionRepository
│   ├── get_user_homework_submissions_use_case.py # Inject HomeworkSubmissionRepository
│   ├── get_homework_submission_status_use_case.py # Inject 3 repositories
│   ├── check_overdue_homework_use_case.py   # Inject HomeworkRepository + HomeworkSubmissionRepository
│   ├── rescan_all_homeworks_use_case.py     # Inject HomeworkRepository + HomeworkSubmissionRepository
│   └── event_handlers.py                    # Cập nhật repository dependencies
└── providers.py                             # Khai báo Dishka providers cho 3 repositories
```

## Complexity Tracking

*Không có vi phạm nào cần biện minh (Tất cả đều tuân thủ nguyên tắc Clean DDD và Constitution v1.5.0).*
