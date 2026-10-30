# Implementation Plan: Clean Plain Text Notifications

**Branch**: `033-clean-plain-text-notifications` | **Date**: 2026-10-31 | **Spec**: [specs/033-clean-plain-text-notifications/spec.md](spec.md)

## Summary
Loại bỏ hoàn toàn các ký tự Markdown thô (`**`, `*`, `` ` ``, `[](url)`) khỏi toàn bộ nội dung thông báo (`NotificationPayload`, `fields`, `content`) trong hệ thống. Chuẩn hóa layout tin nhắn theo dạng Plain Text trực quan với emoji, ngắt dòng khoa học để hiển thị hoàn hảo trên Zalo Bot, Discord, In-App Web Notification và Web Push.

## Technical Context
- **Language/Version**: Python 3.12 (FastAPI, SQLAlchemy 2.0, Dishka DI) & TypeScript / React (Ant Design).
- **Primary Dependencies**: `loguru`, `pytest`, `ant-design`.
- **Target Platform**: Cross-platform (Zalo Bot API, Discord Webhook/Bot, Browser PWA Web Push, Web In-App UI).
- **Performance Goals**: Zero overhead, tin nhắn text nhẹ hơn, chuẩn hóa trực tiếp lúc khởi tạo `NotificationPayload`.

## Constitution Check
- **Simplicity & Clean Code**: Không over-engineering regex strip runtime; chuẩn hóa trực tiếp template chuỗi message.
- **Enterprise UTC**: Giữ nguyên xử lý timezone UTC/VN.
- **Regression Prevention**: Giữ nguyên toàn bộ logic nghiệp vụ event handlers và dispatcher, chỉ format lại string text. 161 unit tests tiếp tục pass 100%.

## Project Structure & Files to Modify

### Backend
1. `backend/app/shared/infrastructure/notification/zalo_channel.py`:
   - Bỏ dấu `*` ở `📢 *{payload.title}*` $\rightarrow$ `📢 {payload.title}`.
2. `backend/app/homework/application/event_handlers.py`:
   - Bỏ `**`, bỏ markdown link trong `🔗 Đường dẫn bài tập` và `📋 Lời phê chi tiết`.
3. `backend/app/meeting/application/event_handlers.py`:
   - Bỏ `**` trong thông báo tạo meeting và thông báo điểm danh.
4. `backend/app/permission_request/application/event_handlers.py`:
   - Bỏ `**` trong thông báo nộp đơn xin phép, đổi ca sinh hoạt, phân công trực nhật.
5. `backend/app/duty/notification_handler.py`:
   - Bỏ `**` trong thông báo trực nhật, đổi lịch, nộp minh chứng.
6. `backend/app/billing/application/notification_handler.py`:
   - Bỏ `**`, backticks `` ` `` trong thông báo hóa đơn, mã thanh toán.
7. `backend/app/bonus_point/notification_handler.py`:
   - Bỏ `**` trong thông báo điểm thưởng/kỷ luật.
8. `backend/app/violation/notification_handler.py`:
   - Bỏ `**` trong thông báo vi phạm kỷ luật.
9. `backend/app/auth/account_notification_handler.py`:
   - Bỏ `**`, backtick trong thông báo khôi phục mật khẩu.
10. `backend/app/reminder/application/reminder_dispatcher.py` & `embed_builder.py`:
    - Bỏ `**`, `*`, `` ` ``, markdown links trong nội dung nhắc nhở meeting và bài tập.
11. `backend/app/scripts/test_discord_notification.py`:
    - Cập nhật test payloads tương ứng để đồng bộ.

### Frontend
- Rà soát `frontend/src/features/notification/components/NotificationDetailModal.tsx` để đảm bảo hiển thị đẹp.

## Implementation Tasks (Atomic Checklist)
- [ ] Task 1: Chuẩn hóa `zalo_channel.py` (loại bỏ markdown formatters thô).
- [ ] Task 2: Chuẩn hóa template tin nhắn bài tập (`homework/application/event_handlers.py`).
- [ ] Task 3: Chuẩn hóa template tin nhắn lịch họp (`meeting/application/event_handlers.py`).
- [ ] Task 4: Chuẩn hóa template tin nhắn xin phép & đổi ca (`permission_request/application/event_handlers.py`).
- [ ] Task 5: Chuẩn hóa template tin nhắn trực nhật (`duty/notification_handler.py`).
- [ ] Task 6: Chuẩn hóa template tin nhắn hóa đơn thu phí (`billing/application/notification_handler.py`).
- [ ] Task 7: Chuẩn hóa template tin nhắn điểm thưởng & vi phạm (`bonus_point/notification_handler.py`, `violation/notification_handler.py`).
- [ ] Task 8: Chuẩn hóa tin nhắn nhắc nhở tự động (`reminder_dispatcher.py`, `embed_builder.py`, `account_notification_handler.py`).
- [ ] Task 9: Chạy test suite `pytest` và kiểm toán toàn bộ file không còn markdown thô.
