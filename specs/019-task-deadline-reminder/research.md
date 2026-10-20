# Research: Automated Task & Deadline Reminder System

**Feature**: `019-task-deadline-reminder`
**Date**: 2026-10-21

## 1. Domain Organization & Placement

### Context & Questions
- Hệ thống nhắc nhở tự động liên quan đến nhiều nguồn nghiệp vụ: `homework` (bài tập), `duty` (lịch trực nhật), và `meeting` (đánh giá cuộc họp).
- Cần quyết định: Đặt logic nhắc nhở ở đâu? Tạo domain độc lập (`app/reminder`) hay phân tán vào từng domain (`app/homework`, `app/duty`, `app/meeting`)?

### Decision
- **Tạo domain độc lập `app/reminder/`**:
  - `domain/`: Entity `TaskReminderLog`, Enums `ReminderStage`, `TaskType`, `ReminderStatus`.
  - `infrastructure/`: Model `TaskReminderLogModel` (SQLAlchemy), `TaskReminderLogRepository` kế thừa `BaseRepository`.
  - `application/`: Các Single-Responsibility Use Cases:
    1. `ScanAndSendRemindersUseCase`: Tiếp nhận trigger (từ cron job hoặc manual run), điều phối quét từng loại task, kiểm tra chống lặp thông qua repository, và gửi tin nhắn DM qua `NotificationService`.
    2. `GetPendingTasksUseCase`: Truy vấn các task cần làm sắp đến hạn của một user cụ thể để hỗ trợ API hoặc hiển thị.
  - `providers.py`: Đăng ký Dishka Provider `ReminderModuleProvider`.
  - `jobs/reminder_scanner_job.py`: Scheduled job chạy định kỳ theo APScheduler.
  - `controller.py`: Endpoints cho Admin: `POST /api/v1/reminders/trigger` (manual dry-run/trigger) và `GET /api/v1/reminders/logs` (xem lịch sử).

### Rationale
- Tuân thủ nguyên tắc **Single Responsibility** và **Clean Architecture (Hiến pháp Principle I & VII)**. Tránh biến domain `homework` hoặc `duty` thành nơi xử lý logic chéo (cross-cutting scheduler).
- Domain `reminder` đóng vai trò điều phối đọc dữ liệu từ các domain repositories (`HomeworkRepository`, `DutyRepository`, `MeetingRepository`, `PermissionRequestRepository`), tổng hợp danh sách cần nhắc và phát thông báo qua `NotificationService`.

### Alternatives Considered
- *Phân tán mỗi domain 1 cron job*: Mỗi domain tự viết checker riêng. Nhược điểm: Phân mảnh lịch chạy APScheduler, khó theo dõi tập trung, trùng lặp code gửi DM Discord và cơ chế deduplication.

---

## 2. Notification Dispatching & Discord DM Strategy

### Context & Questions
- Người dùng đã chỉ định rõ: gửi thông báo trực tiếp qua **Discord Bot** (Direct Message - DM).
- Hệ thống đã có `DiscordService.send_message_to_user(user_id=...)` và `NotificationService.send_to_user(payload)`.
- Cần phương án xử lý lỗi khi người dùng chặn DM hoặc chưa liên kết `discord_id`.

### Decision
- Sử dụng `NotificationService.send_to_user(payload)` với `NotificationPayload(category=NotificationCategory.HOMEWORK/DUTY/MEETING, level=WARNING/CRITICAL)`:
  - `NotificationService` đã tích hợp sẵn cơ chế kiểm tra `user.discord_id`, gọi `DiscordService.send_message_to_user`, kèm cơ chế Exponential Backoff retry (tối đa 3 lần).
  - Tự động fallback ghi log `TaskReminderLog(status="DM_BLOCKED" / "FAILED" / "NO_DISCORD_ID")` để thống kê tỷ lệ gửi tin.
  - Định dạng Discord Embed: Tiêu đề rõ ràng theo mức độ khẩn cấp, tên task, deadline giờ VN (UTC+7), thời gian còn lại, link nộp bài trực tiếp trên web (`https://.../homework` hoặc `/duties`).

### Alternatives Considered
- *Tự gọi trực tiếp HTTP Discord REST API trong use case*: Bị cấm bởi Hiến pháp (Principle I & IV: Không gọi trực tiếp web API trong domain/use case, phải qua Infrastructure Service).

---

## 3. Hybrid Scheduling & Deduplication Logic

### Context & Questions
- Yêu cầu người dùng:
  - 4 Khung giờ cố định: `08:00`, `12:00`, `19:30`, `22:00` (UTC+7).
  - 5 Mốc đếm ngược trước deadline: `2 ngày`, `1 ngày`, `12 giờ`, `4 giờ`, `1 giờ`.
- Làm sao để không bị spam tin nhắn nếu mốc cố định và mốc đếm ngược diễn ra gần nhau?

### Decision
- **Cơ chế Lịch chạy (APScheduler Trigger)**:
  - Scheduler cấu hình cronjob chạy **mỗi 30 phút** hoặc **mỗi 1 giờ** (tại phút thứ 0 và 30: `minute="0,30"`, timezone="Asia/Ho_Chi_Minh").
  - Trong mỗi lần chạy:
    1. Kiểm tra xem giờ hiện tại có rơi vào 4 khung giờ cố định (`08:00`, `12:00`, `19:30`, `22:00`) hay không $\rightarrow$ Xác định `ReminderStage.FIXED_0800`, `FIXED_1200`, `FIXED_1930`, `FIXED_2200`.
    2. Đồng thời kiểm tra chênh lệch thời gian giữa hiện tại và deadline của từng task để xác định mốc tương ứng:
       - Còn từ 47h đến 49h: `OFFSET_2D`
       - Còn từ 23h đến 25h: `OFFSET_1D`
       - Còn từ 11h đến 13h: `OFFSET_12H`
       - Còn từ 3.5h đến 4.5h: `OFFSET_4H`
       - Còn từ 0.5h đến 1.5h: `OFFSET_1H`
- **Quy tắc Deduplication (Chống lặp)**:
  - Mỗi bản ghi `TaskReminderLog` lưu bộ khóa: `(task_type, task_id, user_id, reminder_stage)`.
  - Nếu đã tồn tại log cho stage này $\rightarrow$ **Bỏ qua ngay**.
  - **Cooldown Rule**: Nếu user đã nhận bất kỳ thông báo nào cho cùng một task trong vòng **3 giờ qua**, và mốc tiếp theo không phải là cấp độ khẩn cấp cao hơn (`OFFSET_1H`), hệ thống sẽ hoãn gửi để tránh spam liên tục.
- **Freshness Check (Kiểm tra thời gian thực)**:
  - Ngay trước khi gửi tin cho từng user, kiểm tra lại repository:
    - Nếu là Homework: kiểm tra `submission_status` (đã submit chưa).
    - Nếu là Duty: kiểm tra `status == COMPLETED` hoặc đã có `evidence_images`.
    - Nếu là Meeting Evaluation: kiểm tra bản ghi đánh giá đã tồn tại chưa.
    - Kiểm tra có đơn xin nghỉ / xin gia hạn (`PermissionRequest`) ở trạng thái `APPROVED` hay không.

### Alternatives Considered
- *Chạy cron riêng lẻ cho từng mốc (hàng chục trigger)*: Gây phức tạp cho APScheduler. Chạy 1 job điều phối quét mỗi 30 phút hoặc 1 giờ với kiểm tra logic trong use case là giải pháp chuẩn, linh hoạt và dễ kiểm thử bằng unit test.
