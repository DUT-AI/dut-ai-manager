# Quickstart: Hướng Dẫn Kiểm Thử & Chạy Thử Hệ Thống Thông Báo Đa Kênh

**Feature**: `006-multi-channel-notification-expansion`
**Date**: 2026-10-02

## 1. Điều Kiện Tiên Quyết (Prerequisites)

- Máy chủ Backend đang chạy với cấu hình biến môi trường:
  - `DISCORD_BOT_TOKEN` (hoặc mock Discord API trong kiểm thử)
  - `ZALO_BOT_TOKEN` (hoặc mock Zalo client trong kiểm thử)
  - `BACKEND_PUBLIC_URL=http://localhost:8000` (hoặc domain ngrok/cloudflare khi test thực tế)
- Người dùng test có tài khoản với:
  - `discord_id` được gán hợp lệ (ID Discord cá nhân)
  - `zalo_bot_id` được gán hợp lệ (User ID chat với Zalo Bot)

---

## 2. Kịch Bản Kiểm Thử Nhanh (Quick Verification Scenarios)

### Kịch bản 1: Kiểm tra Static Assets Endpoint
1. Khởi động backend (`make backend-dev`).
2. Mở trình duyệt hoặc dùng cURL kiểm tra ảnh meme:
   ```bash
   curl -I http://localhost:8000/static/assets/meme-hoc-bai.webp
   curl -I http://localhost:8000/static/assets/meme-xin-tien.jpeg
   ```
3. **Kết quả mong đợi**: HTTP `200 OK` với header `content-type: image/webp` / `image/jpeg`.

---

### Kịch bản 2: Kiểm thử Thông Báo Hóa Đơn Mới (Billing)
1. Tạo một hóa đơn cho học viên qua API:
   ```bash
   POST /api/v1/billing/
   ```
2. **Kết quả mong đợi**:
   - Discord: Nhận tin nhắn Embed màu tím, tiêu đề `💰 HÓA ĐƠN MỚI CẦN THANH TOÁN`, hiển thị mã `DUTxxxxxx` và đính kèm ảnh `meme-xin-tien.jpeg`.
   - Zalo: Nhận tin nhắn thông báo tiền quỹ/phạt kèm hướng dẫn chuyển khoản.

---

### Kịch bản 3: Kiểm thử Xác Nhận Thanh Toán Thành Công (SePay Webhook)
1. Giả lập SePay gửi webhook thanh toán:
   ```bash
   POST /api/v1/billing/webhook/sepay
   {
     "content": "DUT123456 chuyen tien",
     "transferAmount": 50000,
     "id": "123456"
   }
   ```
2. **Kết quả mong đợi**:
   - Trạng thái hóa đơn chuyển sang `PAID`.
   - Học viên nhận ngay thông báo "Thanh toán thành công" kèm meme tích cực `meme-lam-viec-3.jpeg` trên cả Discord và Zalo.

---

### Kịch bản 4: Chạy Toàn Bộ Test Suite Tự Động
```bash
pytest backend/tests/unit/test_notification_service.py backend/tests/unit/test_billing_notifications.py
```
