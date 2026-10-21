# Research: PWA & Web Push Notification System

**Feature**: `022-pwa-web-push-notifications`
**Date**: 2026-10-21
**Status**: Completed

---

## 1. Kiến trúc Web Push & VAPID Protocol

### Quyết định (Decision)
Sử dụng chuẩn **VAPID (Voluntary Application Server Identification - RFC 8292)** kết hợp với thư viện `pywebpush` trên Backend Python FastAPI và API chuẩn `PushManager` / `Notification` trên Frontend.

### Lý do (Rationale)
- **VAPID là chuẩn mở của W3C và IETF**: Được hỗ trợ trực tiếp bởi mọi trình duyệt hiện đại (Google Chrome, Apple Safari, Mozilla Firefox, Microsoft Edge) và không phụ thuộc vào SDK độc quyền.
- **Chi phí 0 VNĐ**: Hệ thống không cần mua tài khoản Firebase Cloud Messaging (FCM) trả phí hay Apple Developer Account để gửi push notification trên web; hạ tầng push server của Google (FCM Web Push) và Apple (APNs Web Push) tự động phục vụ miễn phí thông qua giao thức Web Push chuẩn.
- **Bảo mật cao**: Cặp khóa VAPID (Public Key / Private Key) đảm bảo chỉ có máy chủ của DUT AI Manager mới có quyền gửi nội dung tới các token thiết bị đã đăng ký.

### Các lựa chọn đã cân nhắc (Alternatives Considered)
- *OneSignal / Firebase Web SDK*: Yêu cầu phụ thuộc vào bên thứ ba, giới hạn số lượng subscriber ở gói miễn phí, có nguy cơ lộ dữ liệu người dùng của trường và phụ thuộc mạng ngoài. Bị loại bỏ.
- *Server-Sent Events (SSE) / WebSocket*: Chỉ hoạt động khi người dùng đang mở tab trang web. Khi đóng tab hoặc tắt màn hình điện thoại, kết nối bị ngắt ngay lập tức, không đáp ứng được mục tiêu thông báo ngoài màn hình khóa.

---

## 2. Hỗ trợ PWA & Web Push trên iOS (Safari 16.4+)

### Quyết định (Decision)
Thiết lập đầy đủ `manifest.json` với chế độ `display: standalone` và xây dựng UI hướng dẫn riêng cho người dùng iPhone/iPad:
- Nếu phát hiện thiết bị iOS và đang chạy trong trình duyệt thông thường (không phải standalone mode): Hiển thị modal/banner ngắn gọn hướng dẫn người dùng nhấn biểu tượng **Share (Chia sẻ)** ➡️ **"Thêm vào Màn hình chính" (Add to Home Screen)**.
- Khi người dùng mở app từ màn hình chính: Kích hoạt prompt xin cấp quyền `Notification.requestPermission()`.

### Lý do (Rationale)
- Từ iOS 16.4, Apple đã chính thức cho phép Web Push Notifications, nhưng với điều kiện **bắt buộc**: Web app phải được cài đặt vào Màn hình chính (Home Screen PWA) và được mở từ icon đó.
- Nếu không có giao diện hướng dẫn này, người dùng iPhone sẽ không biết cách kích hoạt và tưởng rằng ứng dụng không hỗ trợ.

---

## 3. Cấu hình Service Worker & Chiến lược Caching trên Frontend

### Quyết định (Decision)
Tạo tệp `sw.js` đặt tại thư mục gốc `frontend/public/sw.js` (để có scope toàn bộ ứng dụng `/`):
- Lắng nghe sự kiện `push`: Trích xuất payload JSON từ máy chủ (tiêu đề, nội dung, icon, URL đích) và gọi `self.registration.showNotification(...)`.
- Lắng nghe sự kiện `notificationclick`: Đóng thông báo, tìm tab đang mở hoặc mở cửa sổ mới điều hướng đến URL đích (Deep Linking).
- Lắng nghe sự kiện `install` và `activate`: Kích hoạt ngay lập tức (`self.skipWaiting()` và `clients.claim()`).

### Lý do (Rationale)
- Tách bạch rõ ràng giữa Service Worker quản lý Push và logic React component.
- Scope `/` đảm bảo Service Worker có quyền kiểm soát toàn bộ router của Frontend.

---

## 4. Quản lý Đăng ký Thiết bị (Push Subscription Lifecycle) ở Backend

### Quyết định (Decision)
- Tạo bảng cơ sở dữ liệu `push_subscriptions` liên kết với bảng `users`:
  - `user_id`: UUID của người dùng.
  - `endpoint`: URL duy nhất do Push Service của trình duyệt cấp.
  - `p256dh`: Khóa công khai của thiết bị.
  - `auth`: Khóa bí mật xác thực của thiết bị.
  - `user_agent`: Thông tin trình duyệt/hệ điều hành để nhận biết thiết bị.
  - `is_active`: Trạng thái hoạt động.
- Khi Backend gửi Web Push:
  - Nếu Push Service trả về HTTP 404 hoặc 410 (Gone): Tự động đánh dấu `is_active = False` hoặc xóa bản ghi khỏi CSDL (Dead Token Cleanup).
- Tuân thủ nguyên tắc Clean Architecture & DDD của dự án:
  - Sử dụng Single-Responsibility Use Cases: `RegisterPushSubscriptionUseCase`, `UnregisterPushSubscriptionUseCase`.
  - Tích hợp vào hệ thống nhắc nhở `app/reminder/` hiện tại, phát lệnh Web Push bất đồng bộ qua `EventBus` hoặc Background Task, không làm chậm HTTP request chính.
