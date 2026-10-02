# Feature Specification: Kênh Thông Báo Telegram Bot & Bulk Notification

**Feature Branch**: `005-telegram-bot-notification`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Tôi mong muốn tạo 1 chức năng thông báo qua telegram bot, hãy tìm hiểu về chính sách, tôi mong muốn có thể thông báo cho hàng ngàn người dùng, nhưng mỗi lần gửi thông báo chỉ vài chục người thôi"

## Clarifications

### Session 2026-10-02
- Q: Hệ thống nên thực hiện liên kết tài khoản người dùng với Telegram (`telegram_chat_id`) và xử lý hàng đợi gửi thông báo theo kiến trúc nào? → A: Kết nối bot qua Deep Link mã OTP/Token (`t.me/bot?start=token`), lưu `telegram_chat_id` trên `User`, gửi thông báo qua Background Batching Queue (20-30 msg/s) có retry tự động khi gặp mã lỗi HTTP 429.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Người dùng liên kết tài khoản hệ thống với Telegram Bot cá nhân (Priority: P1)

Người dùng (Trainee, Trainer, Leader, Admin) muốn nhận thông báo thời gian thực về lịch học, bài tập, deadline, vi phạm trực tiếp vào Telegram cá nhân. Người dùng vào trang cá nhân/cài đặt, bấm "Kết nối Telegram", hệ thống tạo mã OTP/Deep Link dẫn trực tiếp đến Telegram Bot (`https://t.me/your_bot?start=<OTP_TOKEN>`). Khi người dùng bấm `Start`, Bot tự động xác thực token và lưu `telegram_chat_id` vào thông tin người dùng.

**Why this priority**: Đây là điều kiện tiên quyết bắt buộc theo chính sách của Telegram: Bot không thể chủ động gửi tin nhắn cho người dùng nếu người dùng chưa từng tương tác `/start` với bot.

**Independent Test**: Người dùng tạo yêu cầu liên kết, mở Telegram qua link OTP, bấm `/start`. Kiểm tra `telegram_chat_id` được cập nhật chính xác trên User Model và trạng thái hiển thị "Đã kết nối Telegram".

**Acceptance Scenarios**:

1. **Given** Người dùng chưa liên kết Telegram, **When** Người dùng bấm "Kết nối Telegram" trong Profile/Settings, **Then** hệ thống sinh ra mã token xác thực một lần (hạn 15 phút) và hiển thị nút/QR mở link `t.me/bot?start=<token>`.
2. **Given** Người dùng mở Telegram và bấm `Start`, **When** Bot nhận webhook/lệnh `/start <token>`, **Then** Bot gọi backend xác thực token, gán `telegram_chat_id`, và gửi tin nhắn chào mừng kèm xác nhận liên kết thành công.
3. **Given** Người dùng muốn hủy nhận thông báo, **When** Người dùng bấm "Hủy kết nối Telegram" trên hệ thống, **Then** hệ thống xóa `telegram_chat_id` và ngừng gửi tin nhắn.

---

### User Story 2 - Quản trị viên / Hệ thống gửi thông báo hàng loạt (Bulk/Broadcast Notification) an toàn theo Batch (Priority: P1)

Hệ thống cần gửi thông báo (ví dụ: thông báo lịch họp mới, nhắc deadline bài tập, thông báo khẩn cấp) đến hàng ngàn người dùng đã liên kết Telegram. Quá trình gửi được đẩy vào Hàng đợi ngầm (Background Queue), tự động chia nhỏ thành các batch 20-30 tin nhắn/giây để tuân thủ nghiêm ngặt giới hạn Rate Limit của Telegram Bot API.

**Why this priority**: Đảm bảo gửi tin nhắn ổn định tới hàng ngàn người mà không làm nghẽn tiến trình chính, không bị Telegram chặn vì spam (lỗi HTTP 429).

**Independent Test**: Kích hoạt gửi broadcast cho 500 người dùng liên kết Telegram. Xác minh hệ thống chia thành các lô ~25 tin/giây, hoàn thành toàn bộ sau ~20 giây mà không có lỗi 429 chưa xử lý.

**Acceptance Scenarios**:

1. **Given** một sự kiện cần gửi thông báo đến N người dùng, **When** tác vụ gửi được kích hoạt, **Then** hệ thống đẩy các task gửi tin nhắn vào Background Job Queue.
2. **Given** hàng đợi có hàng trăm/hàng ngàn tin nhắn chờ gửi, **When** worker xử lý, **Then** worker điều tiết tốc độ tối đa 25-30 request/giây (rate limiting).
3. **Given** Telegram API trả về HTTP 429 Too Many Requests kèm `retry_after = X`, **When** worker bắt được lỗi, **Then** worker tạm dừng (backoff) X giây và tự động retry lại các tin nhắn chưa gửi thành công.

---

### User Story 3 - Tích hợp thông báo sự kiện Domain tự động (Meeting, Homework, Violation) qua Telegram (Priority: P2)

Khi có các sự kiện trong hệ thống (Tạo buổi sinh hoạt, sắp hết hạn nộp bài tập, quá hạn đánh giá 24h bị phạt vi phạm, kết quả chấm bài), hệ thống tự động phát Event và Handler gửi thông báo tương ứng qua Telegram cá nhân cho những người dùng liên quan đã kết nối bot.

**Why this priority**: Tăng tỷ lệ hoàn thành bài tập, tham gia họp đúng giờ và phản hồi đánh giá thông qua kênh thông báo tức thời.

**Acceptance Scenarios**:

1. **Given** Trainer tạo buổi sinh hoạt mới có Trainee tham gia, **When** sự kiện `MeetingCreated` được phát ra, **Then** Handler kiểm tra danh sách Trainee, lọc ra những người có `telegram_chat_id` và gửi tin nhắn thông báo chi tiết lịch học kèm link tham gia.
2. **Given** Trainee chưa nộp bài tập sắp đến hạn (còn 2h), **When** cron job kiểm tra, **Then** hệ thống gửi tin nhắn nhắc nhở qua Telegram cho Trainee.

---

### Edge Cases

- **User chặn (Block) Bot hoặc xóa chat**: Telegram trả về lỗi `403 Forbidden: bot was blocked by the user`. Hệ thống ghi nhận log, đánh dấu trạng thái liên kết tạm thời không khả dụng để không tiếp tục gửi tin lỗi.
- **Tin nhắn chứa ký tự đặc biệt trong HTML/MarkdownV2**: Nội dung tin nhắn phải được escape an toàn trước khi gửi đến Telegram API để tránh lỗi cú pháp `400 Bad Request`.
- **Gửi tin nhắn vượt quá 4096 ký tự**: Nếu thông báo dài quá giới hạn 4096 ký tự của Telegram, hệ thống tự động chia nhỏ thành nhiều tin nhắn nối tiếp.
- **Bot Token bị lỗi hoặc mất kết nối mạng**: Có cơ chế Exponential Backoff retry và logging cảnh báo vào monitoring.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI hỗ trợ cấu hình Telegram Bot Token (`TELEGRAM_BOT_TOKEN`) qua biến môi trường.
- **FR-002**: Hệ thống PHẢI cung cấp API tạo mã liên kết một lần (One-Time Token / Deep Link) và Webhook / Polling Handler nhận lệnh `/start <token>` từ Telegram để cập nhật `telegram_chat_id` cho người dùng.
- **FR-003**: Hệ thống PHẢI mở rộng `User` entity với trường `telegram_chat_id: str | None`.
- **FR-004**: Hệ thống PHẢI cung cấp dịch vụ gửi tin nhắn `TelegramBotClient` hỗ trợ định dạng HTML (hoặc Markdown) an toàn.
- **FR-005**: Hệ thống PHẢI thực hiện gửi thông báo qua Background Queue / Batch Worker với cơ chế Rate Limiting (tối đa 25-30 msg/s trên toàn hệ thống).
- **FR-006**: Hệ thống PHẢI tự động xử lý mã lỗi HTTP 429 (`retry_after`) và lỗi 403 (User blocked bot) một cách an toàn.
- **FR-007**: Hệ thống PHẢI hỗ trợ gửi thông báo theo Domain Events (`MeetingCreated`, `HomeworkAssigned`, `ViolationCreated`, `EvaluationReminder`).
- **FR-008**: Giao diện người dùng (Frontend Profile/Settings) PHẢI hiển thị trạng thái kết nối Telegram ("Đã kết nối" / "Chưa kết nối") cùng nút hành động "Kết nối qua Telegram" / "Hủy kết nối".

---

### Key Entities

- **User**: Thêm trường `telegram_chat_id: str | None` và `telegram_username: str | None`.
- **TelegramLinkToken**: Entity/Cache tạm thời lưu `token`, `user_id`, `expires_at` để đối soát khi người dùng bấm Start trên Telegram.
- **TelegramNotificationJob**: Cấu trúc payload của job gửi tin nhắn trong hàng đợi (bao gồm `chat_id`, `text`, `parse_mode`, `priority`, `retry_count`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Người dùng hoàn thành luồng kết nối Telegram qua Deep Link chỉ với 1 click (`/start`) trong vòng dưới 10 giây.
- **SC-002**: Gửi thành công hàng loạt tin nhắn (1.000+ người) với thông lượng ổn định 25-30 msg/s, không bị crash worker hay rơi rụng tin nhắn.
- **SC-003**: Tỷ lệ gửi thành công đạt 100% đối với các `telegram_chat_id` còn hiệu lực.
- **SC-004**: 100% các trường hợp gặp lỗi 429 Rate Limit được tự động retry theo `retry_after` mà không làm gián đoạn toàn bộ hàng đợi.
