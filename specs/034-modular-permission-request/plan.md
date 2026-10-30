# Implementation Plan: Modular Permission Request Use Cases

**Branch**: `034-modular-permission-request` | **Date**: 2026-10-31 | **Spec**: [specs/034-modular-permission-request/spec.md](spec.md)

## Summary
Tách file gộp `backend/app/permission_request/application/use_cases.py` thành 5 file độc lập (1 use case = 1 file). Cập nhật `__init__.py` xuất đầy đủ 7 use cases chuẩn chỉnh tương tự `bonus_point` và `homework`. Cập nhật `controller.py` & `providers.py`, sau đó xóa vĩnh viễn `use_cases.py`.

## Technical Context
- **Language/Version**: Python 3.12 (FastAPI, Dishka DI).
- **Architecture**: Modular Clean Architecture / SRP / Explicit Package Public API (`__all__`).
- **Constraints**: Zero regression, 161 unit tests pass.

## Implementation Tasks (Atomic Checklist)
- [ ] Task 1: Tạo `get_permission_requests_use_case.py` từ `GetPermissionRequestsUseCase`.
- [ ] Task 2: Tạo `create_permission_request_use_case.py` từ `CreatePermissionRequestUseCase`.
- [ ] Task 3: Tạo `update_permission_request_use_case.py` từ `UpdatePermissionRequestUseCase`.
- [ ] Task 4: Tạo `delete_permission_request_use_case.py` từ `DeletePermissionRequestUseCase`.
- [ ] Task 5: Tạo `restore_permission_request_use_case.py` từ `RestorePermissionRequestUseCase`.
- [ ] Task 6: Cập nhật `backend/app/permission_request/application/__init__.py` import từng use case từ file tương ứng và export trong `__all__`.
- [ ] Task 7: Cập nhật imports trong `backend/app/permission_request/controller.py` và `providers.py`.
- [ ] Task 8: Xóa hoàn toàn file `backend/app/permission_request/application/use_cases.py`.
- [ ] Task 9: Chạy `ruff check` và `pytest tests/unit/` để xác thực zero regression.
