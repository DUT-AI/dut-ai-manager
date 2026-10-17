# Tasks: Tách Biệt Use Cases Đơn Nhiệm Miền Xác Thực (Auth Modular Use Cases)

**Feature**: `012-auth-modular-use-cases`  
**Date**: 2026-10-17  
**Status**: Completed  

---

## Danh Sách Nhiệm Vụ (Task Checklist)

### Phase 1: Trích xuất các tệp Use Case Đơn Nhiệm & Domain TokenService
- [x] **TASK-001**: Tạo [token_service.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/domain/token_service.py) chứa `TokenService` với `@staticmethod create_tokens(user)`.
- [x] **TASK-002**: Tạo [authenticate_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/authenticate_use_case.py) chứa `AuthenticateUseCase` độc lập gọi `TokenService.create_tokens`.
- [x] **TASK-003**: Tạo [authenticate_zalo_phone_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/authenticate_zalo_phone_use_case.py) chứa `AuthenticateZaloPhoneUseCase` gọi `TokenService.create_tokens`.
- [x] **TASK-004**: Tạo [refresh_token_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/refresh_token_use_case.py) chứa `RefreshTokenUseCase` gọi `TokenService.create_tokens`.
- [x] **TASK-005**: Tạo [get_me_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/get_me_use_case.py) chứa `GetMeUseCase`.
- [x] **TASK-006**: Tạo [change_password_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/change_password_use_case.py) chứa `ChangePasswordUseCase`.
- [x] **TASK-007**: Tạo [create_account_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/create_account_use_case.py) chứa `CreateAccountUseCase`.
- [x] **TASK-008**: Tạo [forgot_password_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/forgot_password_use_case.py) chứa `ForgotPasswordUseCase`.

### Phase 2: Cấu hình Gói Ứng dụng & Re-export
- [x] **TASK-009**: Tạo [__init__.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/application/__init__.py) xuất khẩu cả 7 use cases, DTOs, `UserAccountHandler` qua danh sách `__all__` đầy đủ theo Constitution Principle VII.

### Phase 3: Chuẩn hóa Điểm Gọi & Xóa Tệp Nguyên Khối Cũ
- [x] **TASK-010**: Cập nhật import và Dishka provider trong [providers.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/providers.py).
- [x] **TASK-011**: Cập nhật import trong [controller.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/auth/controller.py) sang `from app.auth.application import (...)`.
- [x] **TASK-012**: Xóa bỏ hoàn toàn tệp nguyên khối cũ `backend/app/auth/application/use_cases.py` và loại bỏ `BaseAuthUseCase`.

### Phase 4: Kiểm thử & Xác minh Zero Regression
- [x] **TASK-013**: Chạy kiểm tra tĩnh (`grep`) xác nhận không còn bất kỳ dòng tham chiếu nào tới `app.auth.application.use_cases` trong toàn bộ codebase.
- [x] **TASK-014**: Chạy test suite `pytest backend/tests/api/test_auth_api.py -v` và `pytest backend/tests/unit/core/test_auth_deps.py -v` (100% tests passed).
