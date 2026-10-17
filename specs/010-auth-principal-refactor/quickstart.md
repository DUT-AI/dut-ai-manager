# Hướng dẫn Kiểm thử & Vận hành: Tái cấu trúc Định danh Xác thực (Quickstart)

**Feature**: `010-auth-principal-refactor`
**Date**: 2026-10-17

Tài liệu này hướng dẫn cách chạy và kiểm tra tính hợp lệ của việc tái cấu trúc `AuthPrincipal` sau khi triển khai mã nguồn.

---

## 1. Điều kiện Tiên quyết (Prerequisites)

- Môi trường Python ảo của backend đã kích hoạt:
  ```bash
  cd backend
  source .venv/bin/activate  # Hoặc conda activate
  ```
- Cơ sở dữ liệu và biến môi trường đang chạy ổn định (đã cấu hình trong `.env`).

---

## 2. Kịch bản Kiểm thử Tự động (Automated Verification)

Chạy bộ kiểm thử phân quyền và xác thực hiện tại để đảm bảo không bị hồi quy:

```bash
# 1. Chạy unit tests cho các hàm phụ thuộc xác thực trong core
pytest tests/unit/core/test_auth_principal.py -v

# 2. Chạy integration tests kiểm tra phân quyền RBAC và controller
pytest tests/integration/test_rbac.py -v

# 3. Chạy toàn bộ test suite để đảm bảo Zero Regression
pytest tests/
```

**Kết quả kỳ vọng**:
- 100% tests vượt qua (`PASSED`).
- Không có lỗi liên quan đến `AttributeError: 'AuthPrincipal' object has no attribute 'has_permission'`.

---

## 3. Kịch bản Kiểm thử Đầu cuối Thủ công (Manual E2E Scenarios)

### Kịch bản 1: Xác thực bằng API Key (Machine-to-Machine)
1. **Thao tác**: Gửi request gọi API rescan bài tập hoặc API có quyền với header mang API Key:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/homeworks/admin/rescan?dry_run=true" \
     -H "Authorization: Bearer sk-your-system-key"
   ```
2. **Kỳ vọng**:
   - HTTP Status: `200 OK`.
   - Nhật ký kiểm toán: `current_user_id` ghi nhận là `None`, không có bản ghi nào lưu `user_id = 0`.
   - Không có ngoại lệ `IntegrityError` từ cơ sở dữ liệu.

### Kịch bản 2: API Key cố truy cập endpoint người dùng cá nhân
1. **Thao tác**: Gửi request dùng API Key vào endpoint danh sách bài tập của tôi (`/me`):
   ```bash
   curl -X GET "http://localhost:8000/api/v1/homeworks/me" \
     -H "Authorization: Bearer sk-your-system-key"
   ```
2. **Kỳ vọng**:
   - HTTP Status: `403 Forbidden`.
   - Thông báo lỗi: `"Thao tác chỉ dành cho tài khoản người dùng cá nhân"`.

### Kịch bản 3: Xác thực bằng JWT Token người dùng thật
1. **Thao tác**: Đăng nhập lấy access token và gọi API cá nhân:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/homeworks/me" \
     -H "Authorization: Bearer <jwt-access-token>"
   ```
2. **Kỳ vọng**:
   - HTTP Status: `200 OK`.
   - Dữ liệu trả về đúng danh sách bài tập được giao cho người dùng đăng nhập.
