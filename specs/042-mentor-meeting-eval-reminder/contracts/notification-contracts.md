# Contract: Meeting Evaluation Reminder Payload

**Feature**: `042-mentor-meeting-eval-reminder`  
**Date**: 2026-11-01  

---

## 1. Candidate Generation Contract (`MeetingEvaluationTaskScanner`)

Phương thức: `scan_pending_tasks(now: datetime) -> list[ScannedCandidateTask]`

### Candidate Schema:
```python
@dataclass
class ScannedCandidateTask:
    task_type: TaskType              # TaskType.MEETING_EVALUATION
    task_id: int                     # meeting.id
    task_title: str                  # Tiêu đề nhiệm vụ
    user_id: int                     # ID người nhận
    deadline: datetime               # Hạn chót 72h của buổi học (UTC)
    action_url: str                  # "/dashboard/meetings/{meeting_id}"
    stages: list[ReminderStage]      # Danh sách mốc nhắc nhở phù hợp
```

---

## 2. Notification Payload Contract (`UnifiedNotificationDispatcher`)

Khi candidate được chuyển tới `ReminderDispatcher.dispatch()`:

```json
{
  "user_id": 10,
  "title": "⏰ [NHẮC NHỞ HẠN CHÓT] Đánh giá cuộc họp: Đánh giá tổng thể buổi học: Python Workshop",
  "content": "Chào bạn! Bạn có nhiệm vụ Đánh giá tổng thể buổi học: Python Workshop sắp đến hạn nộp.\n\nHạn chót: 04/11/2026 10:00 (Giờ VN - UTC+7)\nThời gian còn lại: 1 ngày 12 giờ\n\nLưu ý: Vui lòng hoàn thành và nộp trước thời hạn trên để tránh bị hệ thống tự động ghi nhận lỗi vi phạm (Violation) vào cuối ngày.\n\nNộp bài ngay tại: https://app.dutai.site/dashboard/meetings/501",
  "category": "MEETING",
  "level": "WARNING",
  "action_url": "https://app.dutai.site/dashboard/meetings/501",
  "task_type": "MEETING_EVALUATION",
  "task_id": 501,
  "reminder_stage": "OFFSET_1D"
}
```
