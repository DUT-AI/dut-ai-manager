# Tasks: Clean Plain Text Notifications

**Input**: Design documents from `/specs/033-clean-plain-text-notifications/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

## Execution Checklist

### Phase 1: Channel Adapter & Common Services
- [X] T001 [P] Chuẩn hóa Zalo notification layout và loại bỏ markdown formatting trong `backend/app/shared/infrastructure/notification/zalo_channel.py`
- [X] T002 [P] Chuẩn hóa thông báo xác thực tài khoản trong `backend/app/auth/account_notification_handler.py`

### Phase 2: Domain Event Handlers (No Markdown)
- [X] T003 [P] Loại bỏ toàn bộ markdown trong thông báo bài tập `backend/app/homework/application/event_handlers.py`
- [X] T004 [P] Loại bỏ toàn bộ markdown trong thông báo lịch họp và điểm danh `backend/app/meeting/application/event_handlers.py`
- [X] T005 [P] Loại bỏ toàn bộ markdown trong thông báo đơn xin phép và đổi ca `backend/app/permission_request/application/event_handlers.py`
- [X] T006 [P] Loại bỏ toàn bộ markdown trong thông báo trực nhật `backend/app/duty/notification_handler.py`
- [X] T007 [P] Loại bỏ toàn bộ markdown trong thông báo hóa đơn thu phí `backend/app/billing/application/notification_handler.py`
- [X] T008 [P] Loại bỏ toàn bộ markdown trong thông báo điểm rèn luyện `backend/app/bonus_point/notification_handler.py`
- [X] T009 [P] Loại bỏ toàn bộ markdown trong thông báo vi phạm kỷ luật `backend/app/violation/notification_handler.py`

### Phase 3: Reminder & Scheduled Jobs
- [X] T010 [P] Chuẩn hóa tin nhắn nhắc việc trong `backend/app/reminder/application/reminder_dispatcher.py` và `backend/app/reminder/application/embed_builder.py`
- [X] T011 [P] Cập nhật test payloads đồng bộ trong `backend/app/scripts/test_discord_notification.py`

### Phase 4: Validation & Quality Control
- [X] T012 Chạy script quét tĩnh xác nhận không còn cú pháp markdown thô nào trong mã nguồn thông báo
- [X] T013 Chạy unit tests backend `uv run --directory backend pytest tests/unit/`
- [X] T014 Chạy kiểm tra build frontend `npm --prefix frontend run build`
