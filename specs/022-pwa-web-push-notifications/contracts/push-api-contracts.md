# API Contracts: Web Push & PWA Notifications

**Base URL**: `/api/v1/notifications`
**Authentication**: Bearer JWT (`Authorization: Bearer <token>`)

---

## 1. Lấy VAPID Public Key

Lấy khóa công khai VAPID của máy chủ để ứng dụng Frontend chuyển thành `Uint8Array` và truyền vào `pushManager.subscribe()`.

- **Endpoint**: `GET /api/v1/notifications/push-public-key`
- **Quyền truy cập**: Bất kỳ người dùng đã đăng nhập (hoặc public client).

### Response (200 OK)
```json
{
  "is_success": true,
  "code": 200,
  "message": "Lấy VAPID Public Key thành công",
  "data": {
    "public_key": "BNb...your_vapid_public_key_base64..."
  }
}
```

---

## 2. Đăng ký Thiết bị nhận Web Push

Lưu trữ thông tin subscription từ `registration.pushManager.subscribe()` vào tài khoản người dùng hiện tại.

- **Endpoint**: `POST /api/v1/notifications/push-subscriptions`
- **Headers**: `Content-Type: application/json`

### Request Body
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/eXampleEndpoint123...",
  "keys": {
    "p256dh": "BLc4x...client_public_key...",
    "auth": "5x1a...client_auth_secret..."
  },
  "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)..."
}
```

### Response (200 OK)
```json
{
  "is_success": true,
  "code": 200,
  "message": "Đăng ký thiết bị nhận thông báo đẩy thành công",
  "data": {
    "subscription_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "is_active": true
  }
}
```

---

## 3. Hủy Đăng ký Thiết bị

Xóa hoặc hủy kích hoạt token thiết bị khi người dùng đăng xuất hoặc tắt thông báo trên thiết bị hiện tại.

- **Endpoint**: `DELETE /api/v1/notifications/push-subscriptions`
- **Headers**: `Content-Type: application/json`

### Request Body
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/eXampleEndpoint123..."
}
```

### Response (200 OK)
```json
{
  "is_success": true,
  "code": 200,
  "message": "Đã hủy đăng ký nhận thông báo trên thiết bị này",
  "data": null
}
```

---

## 4. Gửi Thử nghiệm Thông báo Đẩy (Self Test Push)

Cho phép người dùng hoặc lập trình viên bấm "Gửi thông báo thử nghiệm" ngay trên giao diện để kiểm tra điện thoại có rung chuông và hiện banner thành công hay không.

- **Endpoint**: `POST /api/v1/notifications/test-push`

### Response (200 OK)
```json
{
  "is_success": true,
  "code": 200,
  "message": "Đã gửi thông báo thử nghiệm tới 1 thiết bị đang hoạt động",
  "data": {
    "sent_count": 1,
    "failed_count": 0
  }
}
```
