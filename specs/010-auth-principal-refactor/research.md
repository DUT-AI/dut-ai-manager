# Nghiên cứu Kỹ thuật: Tái cấu trúc Định danh Xác thực (Auth Principal Refactor)

**Feature**: `010-auth-principal-refactor`
**Date**: 2026-10-17

## 1. Vấn đề Kỹ thuật Cốt lõi

Trong mã nguồn hiện tại (`app/core/deps.py`), hàm `get_current_user` đang phục vụ 2 loại xác thực:
1. **API Key (`sk-...`)**: Là yêu cầu từ hệ thống bên ngoài / dịch vụ máy móc. Khi hợp lệ, hệ thống khởi tạo một `UserEntity` giả lập:
   ```python
   system_user = UserEntity(
       id=0,
       name=f"System: {matched_key.name}",
       email=f"system+{matched_key.id}@dutai.site",
       role_ids=[role.id] if role.id else [],
   )
   ```
2. **JWT Access Token**: Là người dùng cá nhân đăng nhập. Sau khi decode token, hệ thống truy vấn cơ sở dữ liệu `user_repo.get_by_id(payload.sub)` để lấy `UserEntity` đầy đủ, dù JWT claims (`AccessTokenPayload`) đã có sẵn `roles` và `permissions`.

### Các rủi ro đã xác định:
- **Foreign Key Violation**: Gán `user_id = 0` vào các bảng có ràng buộc khóa ngoại tới bảng `users`.
- **Logic rác**: Các hàm controller hoặc use case như `get_assigned_to_user(current_user.id)` sẽ truy vấn dữ liệu của người dùng `0`.
- **Overhead I/O**: Hơn 80% endpoint chỉ kiểm tra `hasPermission`, việc nạp toàn bộ thực thể `UserEntity` (gồm cả liên kết Zalo, Discord, sđt) gây chậm phản hồi không cần thiết.

---

## 2. Quyết định Thiết kế (Technical Decisions)

### Quyết định 1: Định nghĩa mô hình `AuthPrincipal` độc lập
- **Quyết định**: Tạo lớp `AuthPrincipal` (Pydantic model) tại `app/core/principal.py` kế thừa `BaseModel`.
- **Cấu trúc trường**:
  - `actor_type: PrincipalType` (`USER` hoặc `API_KEY`).
  - `actor_id: int | None`: Chứa `user_id` nếu là người dùng; chứa `api_key_id` nếu là API Key.
  - `name: str`: Tên người dùng hoặc tên đại diện của API Key.
  - `email: str | None`: Email người dùng hoặc None đối với API Key.
  - `role_names: list[str]`: Danh sách tên vai trò (ví dụ: `["ADMIN"]`, `["LEADER"]`).
  - `permissions: set[str]`: Tập hợp các quyền hạn được cấp.
- **Phương thức hỗ trợ**:
  - `has_permission(permission_name: str) -> bool`: Tự động trả về `True` nếu có vai trò `ADMIN` (case-insensitive), ngược lại kiểm tra `permission_name in self.permissions`.
  - `is_user -> bool`: Kiểm tra `actor_type == PrincipalType.USER`.
  - `is_api_key -> bool`: Kiểm tra `actor_type == PrincipalType.API_KEY`.
  - `user_id -> int`: Trả về `actor_id` nếu là `USER`, ném `BadRequestException(403)` nếu là API Key.
- **Lý do lựa chọn**: Nhẹ, không phụ thuộc ORM, giải quyết triệt để vấn đề `id=0`, tách biệt hoàn toàn tầng Security/Auth khỏi Domain User.
- **Giải pháp thay thế bị bác bỏ**: Kế thừa `UserEntity` hoặc dùng chung `TokenPayload` -> Bị bác bỏ vì `TokenPayload` chỉ dành cho JWT, không biểu diễn được API Key; còn kế thừa `UserEntity` vẫn mang theo các trường rác không liên quan.

### Quyết định 2: Chiến lược tương thích ngược (Backward Compatibility Strategy)
- **Quyết định**:
  - Giữ nguyên alias `CurrentUser = Annotated[AuthPrincipal, Depends(get_current_principal)]`.
  - Vì hầu hết các controller hiện tại chỉ dùng `current_user.has_permission(...)` hoặc truyền `current_user` vào dependency phân quyền, việc chuyển kiểu dữ liệu của `CurrentUser` sang `AuthPrincipal` giúp hơn 90% endpoint giữ nguyên mã nguồn mà không cần sửa đổi.
  - Thêm một dependency mới `CurrentUserEntity = Annotated[UserEntity, Depends(get_current_user_entity)]` dành riêng cho các endpoint thực sự cần đọc/sửa dữ liệu hồ sơ cá nhân của bảng `users` (như profile, avatar, đổi mật khẩu).
- **Lý do lựa chọn**: Giữ vững nguyên tắc Constitution V (API Backward Compatibility) và giảm thiểu rủi ro hồi quy trên diện rộng.

### Quyết định 3: Tối ưu hóa truy vấn xác thực (Fast-path Authorization)
- **Quyết định**:
  - Khi request mang JWT token: Giải mã token, nếu hợp lệ thì khởi tạo `AuthPrincipal` trực tiếp từ claims trong token (`payload.sub`, `payload.name`, `payload.roles`, `payload.permissions`).
  - Không truy vấn Database bảng `users` ở tầng middleware/dependency xác thực mặc định.
  - Thiết lập `set_current_user_id(payload.sub)` cho audit context.
  - Khi request mang API Key: Chỉ query bảng `RoleApiKey` và `Role` để lấy permissions (nhẹ hơn nhiều so với nạp UserEntity), và thiết lập `set_current_user_id(None)` để ngăn chặn việc ghi `user_id = 0` vào audit log.
- **Lý do lựa chọn**: Tăng tốc độ phản hồi API lên 2-5x đối với các request đọc dữ liệu thông thường, đồng thời triệt tiêu lỗi lưu `user_id=0`.

### Quyết định 4: Tương thích với `PermissionChecker` và `hasPermission`
- **Quyết định**:
  - Hàm `PermissionChecker.__call__(self, current_user: CurrentUser) -> AuthPrincipal` nhận vào `AuthPrincipal` và gọi `current_user.has_permission(self.permission)`.
  - Các hàm kiểm tra nhóm `hasTeamLeaderAccess`, `onlyEditOrDeleteYourself` được tinh chỉnh để kiểm tra `current_user.is_user` trước khi truy cập `user_id`. Nếu là Admin hoặc API Key có quyền bypass thì xử lý hợp lệ.
- **Lý do lựa chọn**: Giữ nguyên toàn bộ chữ ký khai báo `dependencies=[hasPermission(...)]` hoặc `_: Annotated[CurrentUser, hasPermission(...)]` trong các controller.
