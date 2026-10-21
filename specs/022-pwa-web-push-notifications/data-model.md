# Data Model: PWA & Web Push Notification System

**Feature**: `022-pwa-web-push-notifications`
**Date**: 2026-10-21
**Status**: Completed

---

## 1. Thực thể Thực thể Nghiệp vụ (Entities)

### PushSubscription (Đăng ký thiết bị nhận thông báo đẩy)
Đại diện cho một thiết bị/trình duyệt của một người dùng cụ thể đã cấp quyền và đăng ký nhận thông báo đẩy Web Push với máy chủ.

| Thuộc tính (Field) | Kiểu dữ liệu | Bắt buộc | Mô tả |
| :--- | :--- | :---: | :--- |
| `id` | UUID | Có | Định danh duy nhất của bản ghi đăng ký |
| `user_id` | UUID | Có | ID của người dùng sở hữu thiết bị (liên kết bảng `users.id`) |
| `endpoint` | String (Text) | Có | URL duy nhất của Push Service do trình duyệt cấp (Google FCM, Apple APNs, Mozilla) |
| `p256dh` | String (Text) | Có | Khóa công khai ECDH của client dùng để mã hóa nội dung thông báo |
| `auth` | String (Text) | Có | Khóa bí mật xác thực client sinh ra bởi PushManager |
| `user_agent` | String (255) | Không | Thông tin tóm tắt về trình duyệt/hệ điều hành (ví dụ: `Safari on iOS`, `Chrome on Android`) |
| `is_active` | Boolean | Có | Trạng thái kênh đăng ký còn hoạt động hay không (mặc định: `True`) |
| `created_at` | DateTime (UTC+7)| Có | Thời điểm đăng ký lần đầu |
| `last_used_at`| DateTime (UTC+7)| Không | Thời điểm gần nhất máy chủ gửi thông báo thành công |

---

## 2. Quy tắc Ràng buộc & Toàn vẹn Dữ liệu (Validation Rules)

1. **Unique Endpoint**: Trường `endpoint` phải là duy nhất trên toàn hệ thống (`UNIQUE INDEX`). Nếu cùng một thiết bị đăng ký lại (ví dụ sau khi user đăng xuất rồi đăng nhập lại bằng tài khoản khác), hệ thống cập nhật `user_id` và kích hoạt lại `is_active = True`.
2. **Quan hệ 1-N (One-to-Many)**: Một người dùng có thể sở hữu nhiều `PushSubscription` đồng thời (ví dụ: 1 điện thoại Android, 1 iPhone, 1 laptop cá nhân).
3. **Cascade Cleanup**: Nếu tài khoản `User` bị xóa khỏi hệ thống, toàn bộ `PushSubscription` liên quan sẽ bị xóa theo (`ON DELETE CASCADE`).
4. **Vô hiệu hóa tự động (Dead Token Handling)**: Khi máy chủ gửi thông báo mà endpoint trả về lỗi HTTP `404 Not Found` hoặc `410 Gone` (người dùng đã xóa app, chặn quyền hoặc token hết hạn), hệ thống tự động cập nhật `is_active = False` hoặc xóa bản ghi để tránh gửi lặp lại vô ích.

---

## 3. Cấu trúc Payload Thông báo Đẩy (Web Push Payload Schema)

Khi máy chủ đẩy một thông báo ra thiết bị qua Service Worker, tải trọng JSON được mã hóa và gửi đi có cấu trúc như sau:

```json
{
  "title": "Nhắc nhở: Lịch họp Lab chiều nay",
  "body": "Buổi sinh hoạt tuần 8 bắt đầu lúc 14:00 tại Phòng Lab AI.",
  "icon": "/icons/icon-192x192.png",
  "badge": "/icons/badge-72x72.png",
  "tag": "meeting-reminder-123",
  "data": {
    "url": "/schedule/meetings/123",
    "notification_id": "9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4",
    "category": "MEETING"
  }
}
```
- `tag`: Chuỗi định danh giúp nhóm các thông báo tương tự, tránh hiển thị tràn lan nhiều thông báo trùng lặp.
- `data.url`: Đường dẫn tương đối trong ứng dụng để Service Worker mở ngay trang chi tiết khi người dùng nhấn vào thông báo.
