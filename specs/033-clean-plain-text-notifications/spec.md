# Feature Specification: Clean Plain Text Notifications

**Feature Branch**: `033-clean-plain-text-notifications`  
**Created**: 2026-10-31  
**Status**: Draft  

## Problem Statement
Hiện tại, các thông báo gửi qua hệ thống (`NotificationPayload`, `ZaloNotificationChannel`, `DiscordNotificationChannel`, In-App Notification Modal, Web Push, Reminder Dispatcher) đang chứa các cú pháp định dạng Markdown thô như `**bold**`, `*italic*`, `[text](url)`, `` `code` ``.
- Khi gửi qua Zalo Bot, Zalo không hỗ trợ cú pháp Markdown chuẩn như Discord, dẫn đến tin nhắn hiển thị thô các ký tự sao `**`, ngoặc vuông `[]()`, backtick `` ` ``, trông lộn xộn và thiếu chuyên nghiệp.
- Khi hiển thị trên In-App Notification Modal (`NotificationDetailModal.tsx`) hoặc Web Push notification, nội dung cũng hiển thị nguyên văn dạng plain text với các ký tự markdown `**...**` làm trải nghiệm đọc bị ảnh hưởng.
- Người dùng yêu cầu: **Chỉnh sửa lại tất cả các thông báo message không được dùng markdown, chỉ cần chuẩn layout, hiển thị được là tốt.**

## Scope & Requirements
1. **Loại bỏ Markdown cú pháp thô khỏi tất cả Notification Content & Fields**:
   - Thay thế toàn bộ cú pháp `**text**` thành chữ thường hoặc viết hoa có cấu trúc (hoặc format rõ ràng).
   - Thay thế cú pháp `[Tên hiển thị](url)` thành hiển thị rõ tên và kèm URL trực tiếp hoặc qua trường `action_url`.
   - Thay thế cú pháp `` `code` `` thành text thuần rõ ràng (ví dụ: mã giao dịch, thời gian).
   - Loại bỏ các ký tự `*` thừa trong lời nhắc hoặc lưu ý.
2. **Chuẩn hóa Layout & Định dạng**:
   - Bố cục thông báo trực quan, phân dòng rõ ràng bằng Emoji (`📢`, `⏰`, `👤`, `📅`, `👉`, `•`, `⚠️`) và thụt lề/ngắt dòng sạch sẽ.
   - Thể hiện rõ ràng: Tiêu đề -> Lời chào -> Chi tiết nội dung -> Các thông số/trường quan trọng -> Hướng dẫn hành động.
3. **Phạm vi Files Backend**:
   - `backend/app/shared/infrastructure/notification/zalo_channel.py`: Tối ưu layout gửi Zalo Bot (bỏ ký tự `*` quanh title, format field sạch đẹp).
   - `backend/app/homework/application/event_handlers.py`: Thông báo bài tập mới, bài tập đã chấm.
   - `backend/app/meeting/application/event_handlers.py`: Thông báo lịch họp mới, điểm danh thành công.
   - `backend/app/permission_request/application/event_handlers.py`: Thông báo đơn xin phép, đổi ca sinh hoạt, phân công trực nhật.
   - `backend/app/duty/notification_handler.py`: Thông báo phân công trực nhật, đổi lịch trực, nộp minh chứng.
   - `backend/app/billing/application/notification_handler.py`: Thông báo hóa đơn mới, xác nhận thanh toán.
   - `backend/app/bonus_point/notification_handler.py`: Thông báo cộng/trừ điểm rèn luyện.
   - `backend/app/violation/notification_handler.py`: Thông báo biên bản vi phạm kỷ luật.
   - `backend/app/auth/account_notification_handler.py`: Thông báo cấp lại mật khẩu.
   - `backend/app/reminder/application/reminder_dispatcher.py` & `embed_builder.py`: Nhắc nhở hạn chót bài tập và lịch họp sắp diễn ra.
4. **Phạm vi Files Frontend**:
   - Kiểm tra hiển thị `NotificationDetailModal.tsx` và `NotificationTable.tsx` để đảm bảo layout hiển thị gọn gàng, hỗ trợ ngắt dòng và các trường thông tin chuẩn chỉ.

## Success Criteria
- Không còn bất kỳ cú pháp markdown `**`, `*`, `` ` ``, `[](url)` trong các message gửi đến người dùng.
- Tin nhắn gửi qua Zalo Bot hiển thị sạch, đẹp, phân đoạn rõ ràng bằng emoji và xuống dòng chuẩn.
- Tin nhắn trên Discord Embed, In-App Modal và Web Push đọc tự nhiên, thân thiện và không bị lộ ký tự markdown thô.
- Toàn bộ unit tests backend pass 100%. Frontend build không lỗi.
