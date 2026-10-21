# Quickstart & Verification Guide: Unified Multi-Channel Notifications

**Feature**: `024-unified-multi-channel-notifications`
**Date**: 2026-10-22
**Status**: Ready for Validation

Tài liệu này cung cấp các kịch bản kiểm thử tích hợp và kiểm thử đơn vị để xác thực rằng toàn bộ hệ thống thông báo đa kênh hoạt động chính xác từ đầu đến cuối (end-to-end).

---

## 1. Unit Tests Verification

Chạy bộ unit test để xác minh logic của Dispatcher, Channel Adapters và Fault Isolation.

```bash
# Chạy toàn bộ test cho notification hub và adapters
pytest backend/tests/unit/test_unified_notification_dispatcher.py -v
pytest backend/tests/unit/test_notification_channels.py -v
```

### Các kịch bản Unit Test cốt lõi:
1. `test_dispatch_saves_in_app_notification_first`: Đảm bảo dù tất cả các external channels lỗi, bản ghi `Notification` vẫn luôn được lưu thành công vào database.
2. `test_dispatch_calls_all_linked_channels`: Khi user có đủ `discord_id`, `zalo_bot_id` và Web Push subscription, cả 3 channels đều được gọi song song.
3. `test_dispatch_fault_isolation`: Giả lập kênh Discord ném ngoại lệ (`Exception("Discord 50007")`), xác nhận kênh Zalo và Web Push vẫn thực hiện thành công và không ném lỗi ra ngoài caller.
4. `test_dispatch_retry_backoff`: Kiểm tra kênh Zalo/Discord thực hiện retry tối đa 3 lần khi gặp sự cố tạm thời trước khi đánh dấu thất bại.

---

## 2. Integration / End-to-End Scenarios

### Kịch bản 1: Phát sinh sự kiện Meeting mới (`MeetingCreated`)
1. **Thao tác**: Gọi API tạo buổi họp mới với danh sách 2 học viên (1 học viên có Discord + Zalo, 1 học viên chỉ có tài khoản web).
2. **Kỳ vọng**:
   - Cả 2 học viên đều có bản ghi trong bảng `notifications` với `category="MEETING"`, `title="📅 LỊCH SINH HOẠT MỚI"`.
   - Học viên 1 nhận được Discord DM Embed (kèm meme `anh-nhac-em-meme-9.webp`) và tin nhắn Zalo Bot.
   - Học viên 2 không phát sinh lỗi, hệ thống bỏ qua các kênh chưa liên kết.

### Kịch bản 2: Phát sinh sự kiện Hóa đơn mới (`InvoiceCreated`)
1. **Thao tác**: Admin tạo hóa đơn tiền quỹ cho học viên.
2. **Kỳ vọng**:
   - Học viên nhận được thông báo In-App, Discord và Zalo với tiêu đề `💳 THÔNG BÁO HÓA ĐƠN`, kèm ảnh `meme-xin-tien.jpeg` và `action_url` trỏ đến chi tiết hóa đơn.

### Kịch bản 3: Kiểm tra Trung tâm Thông báo In-App trên Web
1. **Thao tác**: Đăng nhập tài khoản học viên -> Gọi `GET /notifications/unread-count`.
2. **Kỳ vọng**: Trả về số lượng `unread_count` chính xác.
3. **Thao tác**: Gọi `POST /notifications/read-all`.
4. **Kỳ vọng**: Tất cả thông báo chuyển sang `is_read=True`, `unread_count` trở về 0.

---

## 3. Script kiểm thử giả lập nhanh (CLI Verification)

Sử dụng script có sẵn hoặc script kiểm tra đa kênh để kiểm tra trực tiếp:

```bash
python -m backend.app.scripts.test_discord_notification --user-id 1 --category homework
```
