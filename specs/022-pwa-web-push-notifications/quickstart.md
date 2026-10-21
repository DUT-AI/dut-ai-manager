# Quickstart & Verification Guide: PWA & Web Push Notification System

**Feature**: `022-pwa-web-push-notifications`
**Date**: 2026-10-21
**Reference Documents**: [spec.md](./spec.md) | [data-model.md](./data-model.md) | [contracts/push-api-contracts.md](./contracts/push-api-contracts.md)

---

## 1. Điều kiện Tiên quyết (Prerequisites)

1. **VAPID Keys**: Backend đã được cấu hình cặp khóa VAPID (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIM_EMAIL`) trong tệp `.env`.
2. **HTTPS / Localhost**: Web Push API và Service Worker yêu cầu môi trường an toàn:
   - Trên máy tính phát triển: Chạy qua `localhost` hoặc `127.0.0.1` (trình duyệt tự động coi là môi trường an toàn).
   - Trên điện thoại thật (Android/iOS): Bắt buộc truy cập qua HTTPS (có thể sử dụng ngrok, Cloudflare Tunnel hoặc địa chỉ IP mạng nội bộ có SSL tự ký).
3. **Phiên bản hệ điều hành kiểm thử**:
   - Android: Bất kỳ thiết bị Android nào có cài Chrome / Edge / Cốc Cốc.
   - iOS: Thiết bị iPhone / iPad chạy **iOS 16.4 trở lên**.

---

## 2. Kịch bản Kiểm thử Đầu-Cuối (End-to-End Verification Scenarios)

### Kịch bản 1: Cài đặt PWA & Kích hoạt Thông báo trên Android
1. Mở Chrome trên Android, truy cập vào ứng dụng web DUT AI Manager.
2. Kiểm tra thanh thông báo xuất hiện banner *"Cài đặt DUT AI Manager vào màn hình chính"* (hoặc chọn menu 3 chấm ➡️ *Cài đặt ứng dụng*).
3. Bấm Cài đặt ➡️ Ứng dụng xuất hiện trên màn hình chính như một app độc lập.
4. Mở app từ màn hình chính và đăng nhập tài khoản thành viên.
5. Kiểm tra pop-up/banner xin cấp quyền thông báo ➡️ Bấm **"Cho phép" (Allow)**.
6. **Kỳ vọng**: Màn hình xác nhận *"Đã kích hoạt thông báo đẩy trên thiết bị này"*. Kiểm tra cơ sở dữ liệu bảng `push_subscriptions` thấy bản ghi mới với `user_id` tương ứng.

---

### Kịch bản 2: Cài đặt PWA & Kích hoạt Thông báo trên iOS (Safari 16.4+)
1. Mở Safari trên iPhone, truy cập vào trang web.
2. Kiểm tra banner hướng dẫn hiển thị: *"Để nhận thông báo ngoài màn hình khóa: Nhấn nút Share ➡️ Thêm vào MH chính"*.
3. Nhấn biểu tượng Share trên Safari ➡️ Chọn **"Thêm vào Màn hình chính" (Add to Home Screen)**.
4. Thoát Safari, tìm icon **DUT AI Manager** ngoài màn hình chính iPhone và chạm mở app.
5. Đăng nhập và nhấn nút *"Bật thông báo"* ➡️ Hộp thoại cấp quyền của iOS xuất hiện ➡️ Nhấn **"Cho phép"**.
6. **Kỳ vọng**: Token thiết bị của Apple APNs Web Push được đăng ký thành công lên máy chủ.

---

### Kịch bản 3: Nhận Thông báo khi Ứng dụng đã Đóng hoàn toàn
1. Trên điện thoại đã đăng ký, vuốt đóng hoàn toàn ứng dụng (Kill App).
2. Khóa màn hình điện thoại.
3. Từ máy chủ (hoặc từ tài khoản Admin/Postman), kích hoạt API gửi thông báo thử nghiệm:
   ```bash
   POST /api/v1/notifications/test-push
   Authorization: Bearer <token_admin_hoặc_thành_viên>
   ```
4. **Kỳ vọng**:
   - Trong vòng dưới 5 giây, màn hình điện thoại sáng lên, chuông rung nhẹ và xuất hiện thẻ thông báo của DUT AI Manager với tiêu đề và icon sắc nét.
   - Chạm vào thông báo: Điện thoại mở ứng dụng và chuyển thẳng đến trang được chỉ định trong thông báo.
