# Quickstart & Verification Guide: Automated Task & Deadline Reminder System

**Feature**: `019-task-deadline-reminder`
**Date**: 2026-10-21

## 1. Prerequisites
- Docker PostgreSQL đang chạy cho dự án `dut-ai-manager`.
- Đã cấu hình `DISCORD_BOT_TOKEN` trong `.env` (hoặc mock trong unit test).
- Cơ sở dữ liệu đã chạy migration mới nhất cho bảng `task_reminder_logs`.

---

## 2. Migration Setup

```bash
cd backend
alembic revision -m "create_task_reminder_logs_table"
# Kiểm tra code migration và thực thi:
alembic upgrade head
```

---

## 3. Automated Tests Execution

Chạy toàn bộ các bài test liên quan đến tính năng nhắc việc:

```bash
# 1. Chạy Unit test cho Use Cases & Repository của module Reminder
pytest backend/tests/unit/test_reminder_use_cases.py -v

# 2. Chạy Integration test kiểm tra khả năng phát hiện task trễ & chống lặp (deduplication)
pytest backend/tests/integration/test_reminder_integration.py -v
```

---

## 4. Manual Verification & Trigger via API

### Kích hoạt quét thủ công (Dry-Run / Manual Trigger)
Gửi yêu cầu tới endpoint quản trị viên:

```bash
curl -X POST "http://localhost:8000/api/v1/reminders/trigger" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
```

**Kết quả mong đợi**:
- Trả về JSON theo đúng định dạng hợp đồng [trigger-reminder-response.json](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/019-task-deadline-reminder/contracts/trigger-reminder-response.json).
- Người dùng có `discord_id` nhận được tin nhắn DM trực tiếp từ bot kèm Discord Embed với màu sắc và nội dung cảnh báo chi tiết.
- Các bản ghi được lưu vào bảng `task_reminder_logs`.
- Lần gọi thứ 2 ngay sau đó sẽ trả về `total_reminders_sent: 0` và `total_skipped_already_sent: >0` nhờ cơ chế chống gửi lặp (deduplication).
