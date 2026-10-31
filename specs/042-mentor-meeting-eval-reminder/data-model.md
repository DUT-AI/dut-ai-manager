# Data Model: Nhắc Nhở Mentor Đánh Giá Buổi Học

**Feature**: `042-mentor-meeting-eval-reminder`  
**Date**: 2026-11-01  

---

## 1. Candidate Task Model (`ScannedCandidateTask`)

DTO đại diện cho một nhiệm vụ sắp đến hạn được phát hiện bởi Scanner:

| Trường | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `task_type` | `TaskType` | `TaskType.MEETING_EVALUATION` |
| `task_id` | `int` | ID của buổi học (`meeting.id`) |
| `task_title` | `str` | Tiêu đề nhiệm vụ hiển thị cho người dùng |
| `user_id` | `int` | ID người nhận (Mentor `meeting.created_by` hoặc Trainee `participant.user_id`) |
| `deadline` | `datetime` | Thời hạn đánh giá (`meeting.evaluation_deadline`, chuẩn UTC) |
| `action_url` | `str` | Đường dẫn chuyển hướng `/dashboard/meetings/{meeting.id}` |
| `stages` | `list[ReminderStage]` | Danh sách các mốc nhắc nhở thỏa mãn tại thời điểm quét |

---

## 2. Tiêu Đề & Nội Dung Thông Báo Phân Biệt Vai Trò

### Cho Mentor (Trainer / Người tạo buổi học):
- **Đánh giá tổng thể chưa hoàn thành**:
  - `task_title`: `Đánh giá tổng thể buổi học: {meeting.title}`
  - `content`: Chào bạn! Bạn có nhiệm vụ Đánh giá tổng thể buổi học {meeting.title} sắp đến hạn nộp. Vui lòng hoàn thành trước thời hạn 72h để tránh bị hệ thống ghi nhận lỗi vi phạm.
- **Đánh giá học viên chưa hoàn thành**:
  - `task_title`: `Đánh giá học viên buổi học: {meeting.title}`
  - `content`: Chào bạn! Bạn còn học viên tham gia buổi học {meeting.title} chưa được đánh giá. Vui lòng hoàn tất đánh giá học viên trước thời hạn.

### Cho Học viên (Trainee):
- `task_title`: `Đánh giá buổi học: {meeting.title}`
- `content`: Chào bạn! Bạn có nhiệm vụ Đánh giá Trainer cho buổi học {meeting.title} sắp đến hạn nộp.

---

## 3. Sơ Đồ Quy Trình Quét & Phát Hiện Ứng Viên (Scanning Flow)

```
[Cron Job chạy mỗi 30 phút: scan_and_send_reminders]
                    │
                    ▼
[MeetingEvaluationTaskScanner.scan_pending_tasks(now)]
                    │
                    ▼
     [Tìm các buổi học kết thúc trong 5 ngày qua]
                    │
     ┌──────────────┴──────────────┐
     ▼                             ▼
(Buổi học đã xong &            (Buổi học chưa xong /
 chưa quá hạn 72h)              đã quá hạn 72h)
     │                             │
     │                             ▼
     │                         [Bỏ qua]
     ▼
[Kiểm tra Mentor: meeting.created_by]
     ├─ Chưa có MeetingOverallEvaluation? ──> [Thêm Candidate: Đánh giá tổng thể]
     └─ Còn Trainee chưa được Mentor đánh giá? ──> [Thêm Candidate: Đánh giá học viên]
     │
     ▼
[Kiểm tra Học viên: valid_participants]
     └─ Chưa nộp TraineeToTrainer Evaluation? ──> [Thêm Candidate: Đánh giá buổi học]
                    │
                    ▼
[ReminderDispatcher: Khử trùng lặp qua notification_repo]
                    │
     ┌──────────────┴──────────────┐
     ▼                             ▼
(Đã gửi mốc này rồi)          (Chưa gửi mốc này)
     │                             │
     ▼                             ▼
  [Bỏ qua]               [Gửi Đa Kênh: Discord, In-App, Web Push, Zalo]
```
