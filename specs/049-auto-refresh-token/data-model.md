# Data Model & State Transitions: Tự Động Làm Mới Token Khi Hết Hạn

**Feature**: `049-auto-refresh-token`
**Date**: 2026-11-04

## 1. Mô hình Thực thể & DTOs (Data Models & DTOs)

### 1.1. Client Session State (Frontend)

Mô hình trạng thái quản lý phiên đăng nhập tại máy khách:

```typescript
interface SessionState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  isRefreshing: boolean;
}
```

### 1.2. Token Refresh Request & Response (Backend DTOs)

```python
class RefreshTokenRequest(BaseModel):
    """Payload làm mới token (tùy chọn trong body nếu cookie đã có sẵn)."""
    refresh_token: str | None = None

class TokenResponse(BaseModel):
    """Cặp token trả về khi xác thực hoặc làm mới thành công."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

### 1.3. Pending Request Queue Item (Frontend)

```typescript
interface QueuedRequestItem {
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}
```

---

## 2. Máy Trạng Thái Phiên Làm Việc (Session State Machine)

```
        +------------------------------------------------------+
        |                                                      |
        v                                                      |
+---------------+   Access Token Valid    +------------------+ |
| UNINITIALIZED | --------------------->  |  AUTHENTICATED   | |
+---------------+                         +------------------+ |
        |                                          |           |
        | No Token / Invalid                       | 401 Error |
        v                                          v           |
+---------------+   Refresh Token Valid   +------------------+ |
| UNAUTHENTICATED|<---------------------- |    REFRESHING    |-+
+---------------+   (401 / Expired)       +------------------+
```

### Chi tiết các bước chuyển trạng thái:

1. **`AUTHENTICATED` -> `REFRESHING`**:
   - **Kích hoạt (Trigger)**: Bất kỳ API request nghiệp vụ nào nhận phản hồi HTTP `401 Unauthorized` từ máy chủ.
   - **Hành động (Action)**:
     - Đặt cờ `isRefreshing = true`.
     - Tạm giữ request hiện tại (đánh dấu `_retry = true`).
     - Bất kỳ request nào khác đến sau được đẩy vào `failedQueue`.
     - Gọi `POST /api/v1/auth/refresh` kèm cookie `refresh_token` (hoặc body).

2. **`REFRESHING` -> `AUTHENTICATED` (Thành công)**:
   - **Kích hoạt (Trigger)**: Máy chủ trả về `200 OK` kèm cặp token mới trong Set-Cookie / response body.
   - **Hành động (Action)**:
     - Gọi `processQueue(null)` để giải phóng toàn bộ các request đang chờ trong `failedQueue`.
     - Tái thực thi request ban đầu với cookie mới.
     - Đặt lại cờ `isRefreshing = false`.

3. **`REFRESHING` -> `UNAUTHENTICATED` (Thất bại / Hết hạn hoàn toàn)**:
   - **Kích hoạt (Trigger)**: Máy chủ trả về mã lỗi HTTP `401 Unauthorized` hoặc `400 Bad Request` cho endpoint `/auth/refresh`.
   - **Hành động (Action)**:
     - Gọi `processQueue(error, null)` để từ chối toàn bộ các request đang chờ.
     - Đặt lại cờ `isRefreshing = false`.
     - Dọn dẹp session trong `AuthContext` (`setUser(null)`).
     - Hiển thị thông báo một lần: "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại."
     - Điều hướng an toàn về `/login`.
