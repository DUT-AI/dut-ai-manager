# Feature Specification: Modular Permission Request Use Cases

**Feature Branch**: `034-modular-permission-request`  
**Created**: 2026-10-31  
**Status**: Draft  

## Problem Statement
Tệp `backend/app/permission_request/application/use_cases.py` đang chứa gộp 5 use case khác nhau:
1. `GetPermissionRequestsUseCase`
2. `CreatePermissionRequestUseCase`
3. `UpdatePermissionRequestUseCase`
4. `DeletePermissionRequestUseCase`
5. `RestorePermissionRequestUseCase`

Cần refactor lại module `permission_request` theo chuẩn kiến trúc của dự án (tương tự `bonus_point` và `homework`):
- Mỗi use case nằm ở **một tệp riêng biệt**.
- Tệp `backend/app/permission_request/application/__init__.py` sẽ import và export sạch sẽ tất cả các use cases đơn lẻ này trong `__all__`.
- File cũ `use_cases.py` sẽ bị xóa hoàn toàn.

## Scope & Target Architecture
1. **Tách các use cases ra file riêng biệt** trong thư mục `backend/app/permission_request/application/`:
   - `get_permission_requests_use_case.py` $\rightarrow$ `GetPermissionRequestsUseCase`
   - `create_permission_request_use_case.py` $\rightarrow$ `CreatePermissionRequestUseCase`
   - `update_permission_request_use_case.py` $\rightarrow$ `UpdatePermissionRequestUseCase`
   - `delete_permission_request_use_case.py` $\rightarrow$ `DeletePermissionRequestUseCase`
   - `restore_permission_request_use_case.py` $\rightarrow$ `RestorePermissionRequestUseCase`
   - (Đã có sẵn: `create_change_meeting_request_use_case.py`, `get_permission_request_detail_use_case.py`).
2. **Cập nhật `backend/app/permission_request/application/__init__.py`**:
   - Import từng use case từ file riêng của nó và định nghĩa `__all__`:
     ```python
     from app.permission_request.application.create_change_meeting_request_use_case import CreateChangeMeetingRequestUseCase
     from app.permission_request.application.create_permission_request_use_case import CreatePermissionRequestUseCase
     from app.permission_request.application.delete_permission_request_use_case import DeletePermissionRequestUseCase
     from app.permission_request.application.get_permission_request_detail_use_case import GetPermissionRequestDetailUseCase
     from app.permission_request.application.get_permission_requests_use_case import GetPermissionRequestsUseCase
     from app.permission_request.application.restore_permission_request_use_case import RestorePermissionRequestUseCase
     from app.permission_request.application.update_permission_request_use_case import UpdatePermissionRequestUseCase

     __all__ = [
         "GetPermissionRequestsUseCase",
         "GetPermissionRequestDetailUseCase",
         "CreatePermissionRequestUseCase",
         "CreateChangeMeetingRequestUseCase",
         "UpdatePermissionRequestUseCase",
         "DeletePermissionRequestUseCase",
         "RestorePermissionRequestUseCase",
     ]
     ```
3. **Cập nhật `controller.py` & `providers.py`**:
   - Sử dụng import rõ ràng (từ package `application` hoặc từ từng file đơn lẻ).
4. **Loại bỏ tệp gộp `use_cases.py`**:
   - Xóa `use_cases.py`.
5. **Đảm bảo Zero Regression**:
   - Toàn bộ 161 unit tests tiếp tục pass 100%.

## Success Criteria
- 100% use cases nằm trong file riêng lẻ.
- File `use_cases.py` bị xóa bỏ hoàn toàn.
- `__init__.py` export đầy đủ 7 use cases chuẩn chỉnh.
- Test suite backend 161/161 tests pass.
