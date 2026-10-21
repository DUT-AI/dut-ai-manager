# Quickstart Validation Guide: Upcoming Meeting Attendance Reminder

**Feature**: `023-upcoming-meeting-reminder`  
**Date**: 2026-10-21  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md)

---

## 1. Prerequisites

- Python 3.12+ với môi trường ảo backend đã cài đặt dependencies (`pytest`, `dishka`, `fastapi`, `sqlalchemy`).
- Database PostgreSQL dev đang chạy qua Docker Compose hoặc local (`make up` hoặc `docker compose up -d db`).

---

## 2. Automated Unit & Integration Testing

### 2.1 Kiểm thử Unit Test cho `UpcomingMeetingTaskScanner`
Kiểm tra khả năng quét ứng viên, tính toán mốc nhắc nhở, và lọc chính xác trạng thái người tham gia.

```bash
# Chạy bộ test scanner độc lập
pytest backend/tests/test_upcoming_meeting_scanner.py -v
```

**Kịch bản kiểm thử bao gồm**:
1. Buổi họp diễn ra sau 1 giờ (`OFFSET_1H`): Thành viên `NOT_JOINED` được phát hiện là ứng viên cần nhắc nhở.
2. Thành viên có trạng thái `ABSENT_EXCUSED` (vắng có phép): Được tự động loại trừ khỏi danh sách nhắc nhở.
3. Thành viên có trạng thái `JOINED` (đã điểm danh trước giờ): Được tự động loại trừ khỏi danh sách nhắc nhở.
4. Buổi họp đã kết thúc (`meeting.is_finished(now) == True`): Bị bỏ qua, không quét ứng viên.

### 2.2 Kiểm thử tích hợp Use Case `ScanAndSendRemindersUseCase`
Kiểm tra toàn bộ pipeline từ lúc Scanner phát hiện, qua Deduplication/Cooldown, đến khi Dispatcher phát thông báo.

```bash
# Chạy bộ test tích hợp toàn diện use case scan & send reminders
pytest backend/tests/test_scan_and_send_reminders_use_case.py -v
```

---

## 3. End-to-End Manual Verification (Admin Trigger API)

### 3.1 Chạy thử nghiệm Quét (Dry-run) qua REST API
Admin có thể kiểm tra danh sách thông báo sẽ phát sinh mà không thực sự bắn tin Discord DM:

```bash
curl -X POST "http://localhost:8000/api/v1/reminders/trigger?dry_run=true" \
  -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
  -H "Content-Type: application/json"
```

**Kết quả mong đợi**:
- HTTP Status `200 OK`.
- Response JSON trả về `total_tasks_scanned > 0` và danh sách `details` chứa các mục có `task_type: "MEETING"` và `stage: "OFFSET_1H"`.

### 3.2 Kích hoạt Quét thật và kiểm tra trên Web Frontend
1. Kích hoạt quét thật:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/reminders/trigger?dry_run=false" \
     -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>"
   ```
2. Mở trình duyệt Web tại `http://localhost:5173/dashboard/notifications`.
3. Đăng nhập bằng tài khoản thành viên tham gia buổi họp.
4. Chọn bộ lọc **"📹 Cuộc họp (Meeting)"**:
   - Thấy dòng thông báo nhắc nhở: *"Nhắc nhở cuộc họp sắp diễn ra: [Tên buổi họp]"*.
   - Nhấp vào thông báo $\rightarrow$ Hệ thống tự động đánh dấu đã đọc và điều hướng sang `/dashboard/meetings/{id}`.
5. Kiểm tra ứng dụng Discord: Thành viên nhận được tin nhắn DM trực tiếp từ Bot với màu sắc và nội dung Rich Embed đúng chuẩn.
