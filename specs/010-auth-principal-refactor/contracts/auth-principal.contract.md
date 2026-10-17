# Hợp đồng Giao tiếp: Xác thực và Phân quyền (Auth Principal Contract)

**Feature**: `010-auth-principal-refactor`
**Date**: 2026-10-17

## 1. Hợp đồng Dependencies Tầng Presentation (`app/core/deps.py`)

### 1.1 `CurrentUser`
- **Định nghĩa**: `CurrentUser = Annotated[AuthPrincipal, Depends(get_current_principal)]`
- **Mục đích**: Được inject vào controller để xác thực và kiểm tra quyền cơ bản.
- **Contract Input**: Request Cookie `access_token` HOẶC Header `Authorization: Bearer <token>` HOẶC `Authorization: Bearer sk-...`.
- **Contract Output**: `AuthPrincipal`.
- **Mã lỗi trả về**:
  - `401 Unauthorized`: Khi thiếu token, token hết hạn, hoặc API Key không hợp lệ.

### 1.2 `CurrentUserEntity`
- **Định nghĩa**: `CurrentUserEntity = Annotated[UserEntity, Depends(get_current_user_entity)]`
- **Mục đích**: Dành riêng cho các điểm cuối cần toàn bộ thông tin cá nhân (Zalo, avatar, phone).
- **Contract Input**: Phụ thuộc vào `CurrentUser`.
- **Contract Output**: `UserEntity`.
- **Mã lỗi trả về**:
  - `403 Forbidden`: Khi request đến từ `API_KEY` ("Chỉ áp dụng cho người dùng cá nhân").
  - `401 Unauthorized`: Khi không tìm thấy người dùng trong cơ sở dữ liệu hoặc tài khoản đã bị vô hiệu hóa.

### 1.3 `hasPermission` / `PermissionChecker`
- **Định nghĩa**: `hasPermission(permission: str | Enum)`
- **Mục đích**: Bọc `Depends(PermissionChecker(permission))` kiểm tra quyền của `CurrentUser`.
- **Contract Rule**:
  - Nếu `current_user.has_permission(permission)` là `True`: Cho phép tiếp tục.
  - Ngược lại: Trả về `403 Forbidden` với message: `"Missing required permission: <permission>"`.

---

## 2. Hợp đồng Ngữ cảnh Kiểm toán (`app/core/context.py`)

- **`get_current_user_id() -> int | None`**:
  - Trả về `user_id` (số nguyên dương) nếu request đến từ người dùng thật.
  - Trả về `None` nếu request đến từ API Key hoặc chưa được xác thực.
- **Cam kết**: Tuyệt đối không bao giờ trả về `0` hoặc lưu `0` vào các trường audit `created_by` / `updated_by`.
