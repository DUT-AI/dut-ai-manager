# Mô hình Dữ liệu: Tái cấu trúc Định danh Xác thực (Data Model)

**Feature**: `010-auth-principal-refactor`
**Date**: 2026-10-17

## 1. Sơ đồ Thực thể Định danh (Identity Architecture)

```
                       +-----------------------+
                       |    Incoming Request   |
                       +-----------+-----------+
                                   |
                     [Token Extraction & Verification]
                                   |
                    +--------------+--------------+
                    |                             |
             [Bearer Token (JWT)]         [API Key (sk-...)]
                    |                             |
       +------------v------------+   +------------v------------+
       |   AccessTokenPayload    |   |    RoleApiKey Entity    |
       |  (Claims: sub, roles,   |   |   (Lookup Role & Perms) |
       |     permissions)        |   +------------+------------+
       +------------+------------+                |
                    |                             |
                    +--------------+--------------+
                                   |
                      +------------v------------+
                      |      AuthPrincipal      |
                      |  (Security Context)     |
                      +------------+------------+
                                   |
             +---------------------+---------------------+
             |                                           |
[Fast-path Authorization]                     [Domain Operation]
- PermissionChecker                           - Read/Write Business Entity
- hasPermission()                             - Optional: Fetch UserEntity
- Audit Context (user_id)                       if human profile required
```

---

## 2. Chi tiết Mô hình (Model Definitions)

### 2.1 Enum `PrincipalType`
Xác định chủng loại chủ thể đang gửi yêu cầu xác thực.

| Giá trị | Mô tả | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- |
| `USER` | Người dùng thật (Human User) | Đăng nhập qua tài khoản (JWT). Có `user_id` thật, có hồ sơ cá nhân. |
| `API_KEY` | Dịch vụ máy móc (Service / API Key) | Gọi tự động từ hệ thống ngoài (`sk-...`). Không có `user_id` trong bảng người dùng. |

### 2.2 Model `AuthPrincipal` (app/core/principal.py)

| Thuộc tính | Kiểu dữ liệu | Bắt buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `actor_id` | `int \| None` | Không | `user_id` nếu `actor_type == USER`; `api_key_id` nếu `actor_type == API_KEY`. |
| `actor_type` | `PrincipalType` | Có | Loại chủ thể (`USER` hoặc `API_KEY`). |
| `name` | `str` | Có | Tên hiển thị người dùng hoặc tên định danh API Key (ví dụ `System: Bot Sync`). |
| `email` | `str \| None` | Không | Email của người dùng; `None` đối với API Key. |
| `role_names` | `list[str]` | Có (Mặc định `[]`) | Danh sách tên vai trò (ví dụ: `["ADMIN"]`, `["LEADER"]`). |
| `permissions` | `set[str]` | Có (Mặc định `set()`) | Tập hợp các chuỗi mã quyền hạn (ví dụ: `{"homework.read", "meeting.create"}`). |

#### Quy tắc Xác thực và Logic Nghiệp vụ (Validation Rules):
1. **`has_permission(permission_name: str) -> bool`**:
   - Nếu có bất kỳ vai trò nào trong `role_names` là `admin` (không phân biệt chữ hoa/thường): Trả về `True`.
   - Ngược lại: Trả về `permission_name in self.permissions`.
2. **`is_user -> bool`**:
   - Trả về `self.actor_type == PrincipalType.USER`.
3. **`is_api_key -> bool`**:
   - Trả về `self.actor_type == PrincipalType.API_KEY`.
4. **`user_id -> int`**:
   - Nếu `self.is_user` và `self.actor_id is not None`: Trả về `self.actor_id`.
   - Nếu là `API_KEY`: Ném ngoại lệ `BadRequestException(403, "Thao tác chỉ dành cho tài khoản người dùng cá nhân")`.

---

## 3. Chuyển đổi và Tương thích (Mapping & Compatibility)

| Nguồn đầu vào | `actor_type` | `actor_id` | `name` | `email` | `permissions` | Audit `current_user_id` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **API Key (`sk-...`)** | `PrincipalType.API_KEY` | `key.id` | `System: {key.name}` | `None` | Lấy từ `RoleRepository` | `None` (Ngăn gán `id=0`) |
| **JWT Access Token** | `PrincipalType.USER` | `payload.sub` | `payload.name` | `payload.email` | `set(payload.permissions)` | `payload.sub` (ID người dùng thật) |

---

## 4. Tách biệt Thực thể Nghiệp vụ (`UserEntity`)

- `UserEntity` giữ nguyên vai trò là **Domain Entity** thuần túy trong `app/user/domain/entity.py`.
- Không bị can thiệp hay ép tạo dữ liệu giả trong luồng middleware/security.
- Khi một điểm cuối thực sự cần truy cập `UserEntity`, nó sử dụng dependency `CurrentUserEntity`, dependency này sẽ kiểm tra `principal.is_user` trước khi truy vấn cơ sở dữ liệu `UserRepository.get_by_id(principal.user_id)`.
