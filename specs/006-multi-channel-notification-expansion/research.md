# Research: Nâng Cấp Hệ Thống Thông Báo Đa Kênh (Discord & Zalo) & Tích Hợp Assets Meme

**Feature**: `006-multi-channel-notification-expansion`
**Date**: 2026-10-02

## 1. Phục Vụ Hình Ảnh Meme Tĩnh (Static Asset URLs for Discord & Zalo)

### Decision
- Mount thư mục `backend/app/assets` thành đường dẫn tĩnh `/static/assets` trong FastAPI bằng `StaticFiles(directory=...)`.
- Xây dựng một helper `get_asset_url(asset_name: str) -> str | None` kết hợp với `settings.BACKEND_PUBLIC_URL` (hoặc `BASE_URL`) để sinh URL tuyệt đối (e.g. `https://api.dut-ai-club.com/static/assets/meme-hoc-bai.webp`).

### Rationale
- Cả Discord API (Embed image/thumbnail) và Zalo Bot Platform (Photo message payload) đều yêu cầu URL hình ảnh công khai có thể truy cập qua giao thức HTTPS.
- Việc mount thư mục `assets` có sẵn giúp hệ thống tái sử dụng 100% kho ảnh hiện hữu mà không cần upload lại lên MinIO hay bên thứ 3.

### Alternatives Considered
- *Upload từng ảnh lên MinIO S3 khi khởi động*: Phức tạp không cần thiết, làm chậm thời gian startup của server và phụ thuộc vào MinIO bucket policy.
- *Gửi raw binary file trực tiếp qua multipart request*: Tốn băng thông gửi nhiều lần, Discord Bot DM và Zalo Bot API xử lý chậm hơn nhiều so với việc trỏ qua URL CDN/Static.

---

## 2. Chuẩn Hóa Unified Notification Service & Dispatcher

### Decision
- Xây dựng lớp dịch vụ `NotificationService` (hoặc `NotificationDispatcher`) nằm trong `app/shared/infrastructure/` hoặc `app/notification/` phụ trách:
  1. Tiếp nhận `NotificationMessage` (tiêu đề, nội dung, màu sắc, link hành động, tên file asset ảnh meme).
  2. Tra cứu thông tin người dùng (`discord_id`, `zalo_bot_id`).
  3. Phân phối song song (concurrent) qua `DiscordService` và `ZaloBotClient` bằng `asyncio.gather(..., return_exceptions=True)`.
  4. Áp dụng Exponential Backoff Retry (tối đa 3 lần) cho từng kênh riêng biệt nếu gặp lỗi mạng tạm thời hoặc Rate Limit (HTTP 429).
  5. Tự động Fallback: Nếu không tìm thấy file asset hoặc URL ảnh bị lỗi, tự động hạ cấp xuống gửi tin nhắn văn bản thuần/Embed không ảnh.

### Rationale
- Hiện tại các notification handler (`ViolationNotificationHandler`, `HomeworkNotificationHandler`, `MeetingNotificationHandler`, `BonusPointNotificationHandler`) đang tự viết code gửi Discord và Zalo lặp đi lặp lại, dẫn đến trùng lặp mã nguồn và khó đồng bộ giao diện meme.
- Đóng gói việc gửi tin vào một Notification Dispatcher duy nhất tuân thủ nguyên tắc DRY và Single Responsibility, giúp các Domain Event Handlers chỉ cần gọi `await notification_service.send(...)`.

---

## 3. Tích Hợp Đầy Đủ Cho Billing Domain (Hóa Đơn & Thanh Toán Thành Công)

### Decision
- Định nghĩa 2 Domain Events trong `app/billing/domain/events.py`:
  - `InvoiceCreated(invoice_id, user_id, amount, reference_code, description, billing_period)`
  - `InvoicePaid(invoice_id, user_id, amount, reference_code, transaction_id, paid_at)`
- Phát sự kiện `InvoiceCreated` trong `CreateInvoiceUseCase` và `CreateMonthlyInvoicesUseCase`.
- Phát sự kiện `InvoicePaid` trong `HandleSePayWebhookUseCase` khi SePay webhook xác nhận chuyển khoản hợp lệ.
- Tạo `BillingNotificationHandler` đăng ký với `EventBus` trong `bootstrap_events`.

### Rationale
- Đảm bảo tuân thủ nghiêm ngặt **Nguyên tắc IV (Event-Driven Decoupling)** và **Nguyên tắc VII (Single-Responsibility Use Cases)** của Constitution: Use case thanh toán không trực tiếp gọi API gửi tin của bên thứ 3 mà thông qua EventBus bất đồng bộ.

---

## 4. Ánh Xạ Kho Ảnh Meme Cho Từng Ngữ Cảnh Use Case

| Ngữ cảnh nghiệp vụ | Domain & Event | Tệp Meme được ánh xạ (`backend/app/assets`) | Màu Embed Discord |
| :--- | :--- | :--- | :--- |
| **Giao bài tập mới** | `HomeworkAssigned` | `meme-hoc-bai.webp` / `meme-lam-viec.webp` | Xanh dương (`0x3498DB`) |
| **Chấm điểm bài tập** | `HomeworkGraded` | `meme-lam-viec-2.jpeg` / `meme-hoc-bai.webp` | Xanh lục (`0x2ECC71`) |
| **Lập biên bản vi phạm** | `ViolationCreated` | `meme-doi-no-2.jpg` / `meme-khoc.webp` | Đỏ (`0xE74C3C`) |
| **Xóa/Hủy vi phạm** | `ViolationUpdated` | `meme-lam-viec-3.jpeg` | Xám (`0x95A5A6`) |
| **Cộng điểm thưởng** | `BonusPointCreated` (>0) | `meme-ngac-nhien.jpeg` | Vàng kim (`0xF1C40F`) |
| **Trừ điểm thưởng** | `BonusPointCreated` (<0) | `meme-khoc-2.jpg` | Cam (`0xE67E22`) |
| **Phát hành hóa đơn / Đóng tiền** | `InvoiceCreated` | `meme-xin-tien.jpeg` / `meme-doi-no-2.jpg` | Tím đậm (`0x9B59B6`) |
| **Thanh toán thành công** | `InvoicePaid` | `meme-lam-viec-3.jpeg` / `meme-lam-viec-4.jpeg` | Xanh lá đậm (`0x27AE60`) |
| **Lên lịch buổi học mới** | `MeetingCreated` | `anh-nhac-em-meme-9.webp` | Xanh dương đậm (`0x2980B9`) |
| **Cập nhật lịch học** | `MeetingUpdated` | `meme-met-moi-lam-viec.jpg` | Cam vàng (`0xF39C12`) |
| **Điểm danh thành công** | `ParticipantCheckedIn` | `meme-lam-viec.webp` | Xanh ngọc (`0x1ABC9C`) |
| **Đơn xin phép mới** | `PermissionRequestCreated` | `anh-nhac-em-meme-9.webp` | Vàng nhạt (`0xF1C40F`) |
