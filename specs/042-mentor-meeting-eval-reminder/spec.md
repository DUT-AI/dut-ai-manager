# Feature Specification: Nhắc Nhở Mentor/Trainer Hoàn Tất Đánh Giá Buổi Học (Mentor Meeting Evaluation Reminder)

**Feature Branch**: `042-mentor-meeting-eval-reminder`  
**Created**: 2026-11-01  
**Status**: Draft  
**Input**: Phản ánh từ người dùng "Hiện tại tôi thấy hệ thống thông báo nhắc nhở mentor đánh giá meeting chưa hoạt động, tôi thấy nó không thông báo cho tôi".

---

## 🎯 Bối cảnh & Vấn đề Cần Giải Quyết

Hiện tại trong hệ thống nhắc việc định kỳ (`ReminderModule`):
1. **Bỏ quên Mentor/Trainer trong Scanner**:
   - `MeetingEvaluationTaskScanner` hiện tại chỉ lặp qua danh sách `valid_participants` (học viên/Trainee).
   - Mentor/Trainer/Creator của buổi họp (`meeting.created_by`) hoàn toàn **không được quét**, dẫn đến Mentor không bao giờ nhận được thông báo nhắc nhở nộp đánh giá.
2. **Mentor có 2 nghĩa vụ đánh giá bắt buộc**:
   - **Đánh giá tổng thể buổi học (`MeetingOverallEvaluation`)**: Đánh giá 4 tiêu chí chung về chất lượng buổi sinh hoạt. Nếu không nộp sau 72h, job phạt vi phạm (`CheckEvaluationDeadlineJobUseCase`) sẽ phạt Mentor! Nhưng trước đó, hệ thống lại không hề gửi bất kỳ thông báo nhắc nhở nào cho Mentor.
   - **Đánh giá từng học viên tham gia (`TrainerToTrainee Evaluation`)**: Mentor đánh giá các Trainee có mặt trong buổi học.
3. **Lệch hạn chót đánh giá (`evaluation_deadline`) giữa 24h và 72h**:
   - Thuộc tính `meeting.evaluation_deadline` trong `Meeting` domain entity hiện đang tính là `end_time + timedelta(hours=24)`.
   - Trong khi quy định chuẩn của hệ thống (trong `backend/app/meeting/domain/constants.py` và spec `038-violation-delay`) là **72 giờ** (`MEETING_EVALUATION_DEADLINE_HOURS = 72`).
   - Do đó, sau 24h, `meeting.is_evaluation_expired(now)` trả về `True`, khiến Scanner coi như buổi họp đã hết hạn và dừng quét sớm, bỏ lỡ 48h nhắc nhở tiếp theo!
4. **Sai lệch `action_url`**:
   - Scanner đang sinh link: `/dashboard/meetings/{meeting.id}/evaluate` (route này không tồn tại trong frontend router).
   - Route chuẩn trên frontend là `/dashboard/meetings/{meeting.id}`.

---

## 👥 User Scenarios & Acceptance Criteria

### User Story 1 - Nhắc nhở Mentor nộp đánh giá tổng thể buổi học (Priority: P1) 🎯 MVP

Là một Mentor/Trainer (người phụ trách hoặc tạo buổi học), tôi muốn nhận được thông báo nhắc nhở đa kênh (In-App, Discord, Web Push, Zalo) khi sắp đến hạn nộp Đánh giá tổng thể buổi học (`MeetingOverallEvaluation`), để tôi không bị hệ thống tự động phạt vi phạm sau 72 giờ.

**Why this priority**: Giải quyết trực tiếp phản ánh của người dùng, bảo vệ Mentor khỏi bị phạt vi phạm oan do quên đánh giá.

**Independent Test**:
- Tạo một buổi học có `enable_evaluation=True`, kết thúc cách đây vài giờ, chưa có bản ghi `MeetingOverallEvaluation`.
- Chạy `ScanAndSendRemindersUseCase` tại thời điểm phù hợp với một ReminderStage.
- Xác nhận Mentor (`meeting.created_by`) nhận được thông báo nhắc nhở hoàn tất đánh giá tổng thể với đường dẫn `/dashboard/meetings/{id}`.

**Acceptance Scenarios**:
1. **Given** buổi học có bật đánh giá, đã kết thúc và Mentor chưa nộp đánh giá tổng thể, **When** tiến trình quét nhắc nhở chạy, **Then** hệ thống phát hiện Mentor là ứng viên cần gửi thông báo nhắc việc.
2. **Given** Mentor đã nộp đánh giá tổng thể thành công, **When** tiến trình quét chạy tiếp theo, **Then** hệ thống không gửi thêm thông báo nhắc đánh giá tổng thể cho buổi học đó nữa.

---

### User Story 2 - Nhắc nhở Mentor hoàn tất đánh giá các học viên tham gia (Priority: P2)

Là một Mentor/Trainer, tôi muốn nhận được nhắc nhở nếu trong buổi học vẫn còn học viên tham gia thực tế mà tôi chưa chấm điểm/đánh giá, để đảm bảo tất cả học viên đều nhận được phản hồi học tập kịp thời.

**Why this priority**: Đảm bảo chất lượng đào tạo, học viên có điểm hoạt động và feedback đầy đủ sau mỗi buổi học.

**Independent Test**:
- Buổi học có 3 học viên tham gia, Mentor mới đánh giá 1 bạn, còn 2 bạn chưa đánh giá.
- Scanner phát hiện Mentor còn thiếu đánh giá học viên và sinh candidate nhắc nhở Mentor.

---

### User Story 3 - Chuẩn hóa hạn chót 72h và đường dẫn chính xác (Priority: P3)

Là một người dùng hệ thống, tôi muốn thời hạn đánh giá buổi học được tính nhất quán là 72 giờ (thay vì bị ngắt sau 24h) và bấm vào thông báo dẫn thẳng đến đúng trang chi tiết buổi họp.

**Why this priority**: Thống nhất Single Source of Truth giữa Domain Entity, Job phạt vi phạm và Scanner nhắc nhở.

**Acceptance Scenarios**:
1. **Given** buổi họp có `end_time`, **Then** `meeting.evaluation_deadline` trả về chính xác `end_time + timedelta(hours=72)`.
2. **Given** thông báo nhắc nhở đánh giá, **Then** trường `action_url` luôn trỏ tới `/dashboard/meetings/{meeting_id}`.

---

## 📋 Functional Requirements

- **FR-001**: Cập nhật `Meeting.evaluation_deadline` trong `backend/app/meeting/domain/meeting.py` sử dụng hằng số `MEETING_EVALUATION_DEADLINE_HOURS = 72`.
- **FR-002**: Bổ sung `overall_eval_repo: MeetingOverallEvaluationRepository` vào `MeetingEvaluationTaskScanner` và `MeetingModuleProvider`.
- **FR-003**: Trong `MeetingEvaluationTaskScanner.scan_pending_tasks()`:
  - Nếu buổi học chưa có đánh giá tổng thể (`not overall_eval_repo.exists_for_meeting(meeting.id)`), sinh `ScannedCandidateTask` gửi tới Mentor (`meeting.created_by`) với tiêu đề: *"Đánh giá tổng thể buổi học: {meeting.title}"*.
  - Kiểm tra xem Mentor đã đánh giá đủ tất cả học viên tham gia (`valid_participants`) hay chưa. Nếu còn học viên chưa được đánh giá, sinh `ScannedCandidateTask` nhắc Mentor hoàn tất đánh giá học viên.
- **FR-004**: Cập nhật `action_url` chuẩn thành `/dashboard/meetings/{meeting.id}`.
- **FR-005**: Mở rộng phạm vi tìm kiếm buổi họp `start_date` trong `meeting_repo.get_all_with_participants` từ 3 ngày thành 5 ngày (`now - timedelta(days=5)`) để đảm bảo bao trọn khung giờ 72h.

---

## 🎯 Success Criteria

- **SC-001**: 100% các Mentor phụ trách buổi học có bật đánh giá đều nhận được thông báo nhắc nhở trước khi hết hạn 72h nếu chưa nộp đánh giá.
- **SC-002**: Không phát sinh trùng lặp thông báo nhờ cơ chế Deduplication theo `(task_type, task_id, user_id, reminder_stage)`.
- **SC-003**: 100% unit & integration test liên quan đến `MeetingEvaluationTaskScanner` và `ReminderModule` đều passed.
