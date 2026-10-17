# Research & Decision Record: Tách Biệt Use Cases Đơn Nhiệm Miền Xác Thực (Auth)

**Feature**: `012-auth-modular-use-cases` | **Date**: 2026-10-17

## 1. Khảo Sát Hiện Trạng Tệp `use_cases.py`

Tệp `backend/app/auth/application/use_cases.py` hiện dài ~395 dòng chứa:
1. `BaseAuthUseCase`: Lớp cơ sở cung cấp method `create_tokens(user)` và lưu trữ `account_repo`, `user_repo`.
2. `AuthenticateUseCase(BaseAuthUseCase)`: Xác thực email & password, kiểm tra active status, trả về `(UserEntity, access_token, refresh_token)`.
3. `AuthenticateZaloPhoneUseCase(BaseAuthUseCase)`: Xác thực số điện thoại Zalo, mapping tài khoản.
4. `RefreshTokenUseCase(BaseAuthUseCase)`: Xác thực refresh token, tạo cặp access/refresh token mới.
5. `GetMeUseCase`: Tra cứu thông tin chi tiết của user theo `user_id`.
6. `ChangePasswordUseCase(BaseAuthUseCase)`: Đổi mật khẩu cho user.
7. `CreateAccountUseCase`: Đăng ký tài khoản cho user ID có sẵn.
8. `ForgotPasswordUseCase(BaseAuthUseCase)`: Reset password ngẫu nhiên và bắn sự kiện `ForgotPasswordRequested` qua `EventBus`.

## 2. Điểm Gọi Phụ Thuộc (Call Sites)

- **`backend/app/auth/providers.py`**:
  Đang import:
  ```python
  from app.auth.application.use_cases import (
      AuthenticateUseCase,
      AuthenticateZaloPhoneUseCase,
      ChangePasswordUseCase,
      CreateAccountUseCase,
      ForgotPasswordUseCase,
      GetMeUseCase,
      RefreshTokenUseCase,
  )
  ```
- **`backend/app/auth/controller.py`**:
  Đang import:
  ```python
  from app.auth.application.use_cases import (
      AuthenticateUseCase,
      AuthenticateZaloPhoneUseCase,
      ChangePasswordUseCase,
      CreateAccountUseCase,
      ForgotPasswordUseCase,
      GetMeUseCase,
      RefreshTokenUseCase,
  )
  ```
- **Không có nơi nào khác trong toàn bộ dự án phụ thuộc trực tiếp vào `use_cases.py`**.

## 3. Quyết Định Thiết Kế

1. **Xử lý BaseAuthUseCase**:
   - Tách thành tệp riêng `base_auth_use_case.py`.
   - Các use case kế thừa (`AuthenticateUseCase`, `AuthenticateZaloPhoneUseCase`, `RefreshTokenUseCase`, `ChangePasswordUseCase`, `ForgotPasswordUseCase`) import `BaseAuthUseCase` từ `.base_auth_use_case`.
   - Không bị circular import vì `base_auth_use_case.py` không import bất kỳ use case con nào.
2. **Không duy trì Shim tương thích ngược**:
   - Xóa bỏ hoàn toàn tệp `use_cases.py`.
   - Re-export toàn bộ qua `backend/app/auth/application/__init__.py`.
   - `providers.py` và `controller.py` import trực tiếp từ `app.auth.application`.
