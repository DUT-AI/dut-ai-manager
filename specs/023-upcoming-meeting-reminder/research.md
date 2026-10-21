# Research & Architectural Decisions: Upcoming Meeting Attendance Reminder

**Feature**: `023-upcoming-meeting-reminder`  
**Date**: 2026-10-21  
**Spec**: [spec.md](./spec.md)

---

## 1. Task Scanner Architecture & Strategy Pattern

### Decision
Tạo một lớp Scanner độc lập mang tên `UpcomingMeetingTaskScanner` kế thừa từ interface chuẩn `BaseTaskScanner` (`backend/app/reminder/application/scanners/base_scanner.py`), tuân thủ nghiêm ngặt **Strategy Pattern** và quy tắc Single-Responsibility Use Case (Hiến pháp Nguyên tắc VII & IX).

### Rationale
- Hệ thống nhắc nhở `dut-ai-manager` đã áp dụng kiến trúc Plugin-like Scanners: `ScanAndSendRemindersUseCase` nhận danh sách `scanners: list[BaseTaskScanner]` được Dishka container inject.
- Mỗi scanner chỉ chịu trách nhiệm duy nhất cho một miền nghiệp vụ (Homework, Duty, Meeting Evaluation). Việc tạo `UpcomingMeetingTaskScanner` giữ cho `ScanAndSendRemindersUseCase` hoàn toàn không bị phình to (Zero-bloat) và không bị coupling trực tiếp với các repository của Meeting.
- Tuân thủ quy tắc không dùng Base Use Case hay kế thừa phức tạp, dễ dàng viết Unit Test độc lập bằng cách mock `MeetingRepository`.

### Alternatives Considered
- *Gộp chung vào `MeetingEvaluationTaskScanner`*: Bị từ chối vì vi phạm SRP. `MeetingEvaluationTaskScanner` quét các buổi họp **đã kết thúc** để nhắc người tham gia đánh giá, trong khi `UpcomingMeetingTaskScanner` quét các buổi họp **sắp diễn ra trong tương lai** để nhắc chuẩn bị tham dự và điểm danh.
- *Viết trực tiếp logic vào `ScanAndSendRemindersUseCase`*: Bị từ chối vì vi phạm Open/Closed Principle và Hiến pháp Clean Architecture.

---

## 2. Truy Vấn Dữ Liệu & Tối Ưu Cửa Sổ Thời Gian (Lookahead Window)

### Decision
Sử dụng phương thức truy vấn sẵn có trong `MeetingRepository`:
- Sử dụng `get_all_with_participants(start_date=now, end_date=now + timedelta(days=2), limit=100)` (hoặc `get_upcoming_meetings(start_threshold=now)`).
- Eager load sẵn quan hệ `participants` và `creator` để tránh triệt để vấn đề truy vấn N+1 khi duyệt danh sách người tham gia.

### Rationale
- Các mốc nhắc nhở xa nhất trong hệ thống là `OFFSET_2D` (48 giờ trước) và `OFFSET_1D` (24 giờ trước). Do đó, cửa sổ quét từ thời điểm hiện tại `now` đến `now + 48h` (2 ngày tới) bao phủ 100% tất cả các mốc nhắc nhở cần kích hoạt.
- `MeetingRepository` đã có sẵn cơ chế eager loading `selectinload(ORMMeeting.participants).joinedload(ORMParticipant.user)`, giúp việc lấy thông tin người tham gia diễn ra tối ưu trong đúng 1-2 câu truy vấn SQL.

### Alternatives Considered
- *Quét toàn bộ meeting trong tương lai không giới hạn*: Bị từ chối vì gây tải bộ nhớ không cần thiết khi số lượng meeting tích lũy trong năm lớn.
- *Quét trực tiếp bảng `meeting_participants`*: Bị từ chối vì không tận dụng được Aggregate Root `Meeting` (cần kiểm tra `meeting.is_finished()`, `meeting.start_time`, `meeting.title`, v.v.).

---

## 3. Quy Tắc Lọc Thành Viên & Trạng Thái Tham Gia (Participant Filtering)

### Decision
Lọc danh sách ứng viên nhận nhắc nhở dựa trên trạng thái `ParticipantStatus`:
1. Bỏ qua các bản ghi bị xóa mềm (`p.is_deleted == True`).
2. Bỏ qua các thành viên đã có đơn xin vắng được duyệt (`p.status == ParticipantStatus.ABSENT_EXCUSED`).
3. Bỏ qua các thành viên đã chuyển sang ca họp khác (nếu đã bị xóa hoặc thay thế bằng bản ghi mới ở buổi họp khác).
4. Bỏ qua các thành viên đã thực hiện điểm danh hoặc đã hoàn thành (`p.status in (ParticipantStatus.JOINED, ParticipantStatus.COMPLETED)`).
5. Chỉ nhắc nhở các thành viên chưa điểm danh (`ParticipantStatus.NOT_JOINED`, hoặc các trạng thái chờ).

### Rationale
- Đây là kết quả thống nhất trực tiếp từ người dùng trong phiên làm rõ đặc tả (Clarifications Q2/A2).
- Giúp bảo vệ trải nghiệm của người dùng: thành viên đã báo cáo vắng hợp lệ hoặc đã có mặt tại phòng họp sẽ không bị nhận tin nhắn nhắc nhở spam làm phiền.

### Alternatives Considered
- *Nhắc nhở toàn bộ người trong danh sách kể cả người xin vắng*: Bị loại bỏ vì gây cảm giác phiền toái và thiếu đồng bộ với hệ thống đơn phép.

---

## 4. Mở Rộng Domain Entity & Phân Phối Đa Kênh (Multi-Channel Dispatch)

### Decision
1. Bổ sung giá trị `MEETING = "MEETING"` vào `TaskType` enum trong `backend/app/reminder/domain/entity.py`.
2. Trong `Notification.create_deadline_reminder`:
   - Gắn `TaskType.MEETING` với `NotificationCategory.MEETING`.
   - Điều chỉnh tiêu đề và nội dung thông báo thân thiện riêng cho cuộc họp (thay vì "nhiệm vụ có hạn chót", chuyển thành "cuộc họp sắp diễn ra lúc... vui lòng chuẩn bị tham gia và điểm danh đúng giờ").
3. Tinh chỉnh `build_reminder_embed` trong `backend/app/reminder/application/embed_builder.py`:
   - Nhận diện `TaskType.MEETING` -> Tiêu đề: `⏰ [NHẮC NHỞ LỊCH HỌP] Buổi họp / Sinh hoạt: {task_title}`.
   - Nút hành động trực tiếp dẫn đến: `👉 [Bấm vào đây để xem chi tiết và điểm danh]({action_url})`.
4. Web Push Notification:
   - Gửi payload push tiêu chuẩn với tag `meeting-{meeting_id}` và category `MEETING`.

### Rationale
- Không làm thay đổi cấu trúc bảng cơ sở dữ liệu `notifications` (đã có sẵn cột `task_type VARCHAR`, `task_id INTEGER`, `category VARCHAR`).
- Bảo đảm tính đồng nhất tuyệt đối trên cả 3 kênh: Web In-App, Discord Bot DM, và Web Push (PWA).

### Alternatives Considered
- *Tạo bảng riêng `meeting_reminders`*: Bị từ chối vì vi phạm nguyên tắc hợp nhất thông báo của dự án (Spec 019 đã hợp nhất toàn bộ thông báo vào bảng `notifications`).

---

## 5. Chống Gửi Trùng Lặp & Giãn Cách Cooldown (Idempotency & Cooldown)

### Decision
- Tiếp tục kế thừa 100% cơ chế Deduplication và Cooldown hiện có của `ScanAndSendRemindersUseCase`:
  - `has_reminder_been_sent(task_type="MEETING", task_id=meeting.id, user_id=user.id, stage=stage)`: Ngăn chặn gửi trùng cùng 1 mốc.
  - `is_within_cooldown(...)`: Kiểm tra khoảng cách tối thiểu 3 giờ giữa các lần nhắc, ngoại trừ mốc khẩn cấp 1 giờ trước họp (`OFFSET_1H`) luôn được ưu tiên phát ngay.

### Rationale
- Đảm bảo tính nhất quán giữa tất cả các loại nhiệm vụ trong hệ thống.
- Ngăn ngừa tình trạng spam người dùng khi cronjob chạy lặp lại nhiều lần trong ngày.
