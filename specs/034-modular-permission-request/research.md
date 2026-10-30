# Phase 0: Research & Decision Log

## Decision: Tách Use Cases trong `permission_request/application` thành các file độc lập
- **Mục tiêu**: Tuân thủ chuẩn Single Responsibility Principle (SRP) và mô hình Clean Architecture đồng bộ với các module khác trong hệ thống (`homework/application`, `bonus_point/application`, `meeting/application`).
- **Danh sách file phân rã**:
  1. `get_permission_requests_use_case.py`:
     - Chứa `GetPermissionRequestsUseCase`.
     - Phụ thuộc: `PermissionRequestRepository`, `build_query_support`, `FilterCriterion`, `FilterOperator`.
  2. `create_permission_request_use_case.py`:
     - Chứa `CreatePermissionRequestUseCase`.
     - Phụ thuộc: `PermissionRequestRepository`, `HomeworkRepository`, `EventBus`, `PermissionRequestCreated`.
  3. `update_permission_request_use_case.py`:
     - Chứa `UpdatePermissionRequestUseCase`.
     - Phụ thuộc: `PermissionRequestRepository`, `HomeworkRepository`, `EventBus`, `PermissionRequestUpdated`, `PermissionRequestUpdate`.
  4. `delete_permission_request_use_case.py`:
     - Chứa `DeletePermissionRequestUseCase`.
     - Phụ thuộc: `PermissionRequestRepository`.
  5. `restore_permission_request_use_case.py`:
     - Chứa `RestorePermissionRequestUseCase`.
     - Phụ thuộc: `PermissionRequestRepository`.
- **Package Export (`__init__.py`)**:
  - Re-export toàn bộ 7 use cases (`GetPermissionRequestsUseCase`, `GetPermissionRequestDetailUseCase`, `CreatePermissionRequestUseCase`, `CreateChangeMeetingRequestUseCase`, `UpdatePermissionRequestUseCase`, `DeletePermissionRequestUseCase`, `RestorePermissionRequestUseCase`).
  - Đảm bảo bất kỳ nơi nào import `from app.permission_request.application import ...` đều tương thích 100%.
- **Controller & Providers**:
  - Chuyển import từ `.use_cases` sang các file cụ thể tương ứng.
- **Xóa file cũ**:
  - Xóa `backend/app/permission_request/application/use_cases.py`.
