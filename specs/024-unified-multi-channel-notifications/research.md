# Research & Architecture Decisions: Unified Multi-Channel Notifications

**Feature**: `024-unified-multi-channel-notifications`
**Date**: 2026-10-22
**Status**: Completed

## 1. Technical Context & Current State Analysis

### Current State
Hệ thống `dut-ai-manager` hiện có 2 luồng phát thông báo độc lập và phân mảnh:
1. **Event-driven (Tức thời)**: Các module `meeting`, `homework`, `violation`, `bonus_point`, `billing` sử dụng `NotificationService` (`app/shared/infrastructure/notification_service.py`).
   - *Hạn chế*: Chỉ hỗ trợ Discord và Zalo. **Hoàn toàn không lưu vào cơ sở dữ liệu (In-App DB)**, không gửi Web Push PWA. Do đó, người dùng mở Web Dashboard hoặc Zalo Mini App vào `/notifications/my` không thấy bất kỳ lịch sử thông báo nào về bài tập mới, lịch họp, hay hóa đơn.
2. **Scheduled Reminders (Định kỳ)**: Module `reminder` sử dụng `ReminderDispatcher` (`app/reminder/application/reminder_dispatcher.py`).
   - *Hạn chế*: Lưu vào DB, gửi Web Push, gửi Discord DM, nhưng **không gửi Zalo Bot**. Đồng thời hàm entity `Notification.create_deadline_reminder` bị coupling chặt vào logic đếm ngược deadline, không thể tái sử dụng cho các thông báo thông thường.

---

## 2. Architecture Decisions & Patterns

### Decision 1: Cấu trúc Cổng Điều Phối Hợp Nhất (Unified Notification Hub)
- **Decision**: Xây dựng `UnifiedNotificationDispatcher` đặt tại `app/shared/infrastructure/notification/dispatcher.py` và trừu tượng hóa các kênh qua mẫu thiết kế **Strategy / Adapter Pattern** (`NotificationChannel`).
- **Rationale**:
  - Tuân thủ nguyên tắc **Open-Closed (OCP)**: Khi hệ thống cần tích hợp thêm kênh thứ 5 (Telegram Bot, Email SendGrid, SMS Twilio), chỉ cần tạo mới một lớp kế thừa `NotificationChannel` và đăng ký vào Dishka DI mà không phải sửa đổi bất kỳ dòng code nào trong các module nghiệp vụ.
  - Đảm bảo **Single Source of Truth**: Mọi thông báo dù sinh ra từ Domain Event hay Cronjob Scanner đều đi qua một điểm kiểm soát duy nhất.
- **Alternatives Considered**:
  - *Phương án A: Bổ sung code lưu DB trực tiếp vào `NotificationService` cũ*: Bị từ chối vì không giải quyết được tính mở rộng và vẫn để `ReminderDispatcher` nằm riêng rẽ, tiếp tục duy trì mã trùng lặp.
  - *Phương án B: Đưa `NotificationDispatcher` thành một microservice riêng biệt qua Message Queue (RabbitMQ / Kafka)*: Bị từ chối vì quá tải (over-engineering) so với quy mô hiện tại của CLB, tăng chi phí vận hành hạ tầng không cần thiết.

---

### Decision 2: Chiến lược Điều Phối & Cách Ly Lỗi (Fault Isolation Strategy)
- **Decision**:
  - **In-App Notification (Database)**: Được thực thi trước tiên để đảm bảo tính toàn vẹn dữ liệu (User luôn có thông báo trên Web / Mini App).
  - **External Channels (Discord, Zalo, Web Push)**: Được bọc trong `asyncio.create_task` và chạy song song bằng `asyncio.gather(*tasks, return_exceptions=True)`.
  - Mỗi channel adapter có cơ chế Retry độc lập với Exponential Backoff (tối đa 3 lần).
- **Rationale**:
  - Tuân thủ **Hiến pháp Nguyên tắc IV**: Các tác vụ ngoại vi (external APIs) không được phép chạy đồng bộ gây nghẽn (blocking) giao dịch cơ sở dữ liệu.
  - Đảm bảo sự cố từ Discord (Rate limit 429, người dùng khóa DM 50007) hoặc Zalo Bot (token hết hạn) không làm ảnh hưởng đến các kênh khác và không làm sập tiến trình.
- **Alternatives Considered**:
  - *Gửi tuần tự từng kênh (Sequential)*: Bị từ chối vì nếu Discord timeout (chờ 5 giây), Zalo và Web Push sẽ bị trễ tương ứng.

---

### Decision 3: Chuẩn Hóa Payload & Factory Method cho Domain Entity
- **Decision**:
  - Mở rộng `NotificationPayload` (`app/shared/infrastructure/notification_payload.py`) làm chuẩn giao tiếp chung giữa các Domain và Notification Hub.
  - Mở rộng Domain Entity `Notification` trong `app/reminder/domain/entity.py` (hoặc `app/shared/domain/notification.py`):
    - Cung cấp Factory method `create_event(...)` cho các thông báo thông thường (bài tập, họp, điểm cộng, vi phạm, hóa đơn).
    - Giữ và tái cấu trúc `create_deadline_reminder(...)` chuyên biệt cho luồng đếm ngược hạn chót.
    - Cung cấp trường `metadata_json: dict | None` để lưu trữ linh hoạt dữ liệu ngữ cảnh (ví dụ: `{"invoice_id": 10, "amount": 50000}`).
- **Rationale**:
  - Loại bỏ chuỗi `if-else` cồng kềnh trong việc xác định tiêu đề và nội dung.
  - Đảm bảo các thuộc tính kỹ thuật như `task_type`, `task_id`, `reminder_stage` không gây lỗi khi một thông báo không phải là tác vụ nhắc việc.

---

### Decision 4: Tích Hợp Kho Ảnh Meme & Assets (`backend/app/assets`)
- **Decision**: Giữ nguyên quy ước map meme assets vào các danh mục thông báo:
  - `HOMEWORK`: `meme-hoc-bai.webp`, `meme-lam-viec.webp`
  - `VIOLATION`: `meme-doi-no-2.jpg`, `meme-khoc.webp`
  - `BONUS_POINT` / `BILLING` (Nhắc nợ): `meme-xin-tien.jpeg`, `meme-ngac-nhien.jpeg`
  - `BILLING` (Thanh toán thành công): `meme-lam-viec-3.jpeg`
  - `MEETING` / `DUTY`: `anh-nhac-em-meme-9.webp`, `meme-met-moi-lam-viec.jpg`
- **Rationale**: Đã được chứng minh hiệu quả trong việc tạo sự gần gũi, tương tác cao với sinh viên và thành viên CLB.
