# Research & Technical Decisions: Nhắc Nhở Mentor Đánh Giá Buổi Học

**Feature**: `042-mentor-meeting-eval-reminder`  
**Date**: 2026-11-01  

---

## 1. Vấn Đề Kỹ Thuật & Hiện Trạng

### 1.1 Tại sao Mentor không nhận được thông báo nhắc nhở?
Trong file `backend/app/reminder/application/scanners/meeting_evaluation_scanner.py`:
```python
valid_participants = [
    p for p in meeting.participants
    if not p.is_deleted and p.status in (...)
]
for p in valid_participants:
    evaluated_count = self.evaluation_repo.count_evaluations_by_reviewer(
        meeting_id=meeting.id,
        reviewer_id=p.user_id,
    )
    if evaluated_count == 0:
        candidates.append(...)
```
- Scanner hiện tại **chỉ duyệt qua mảng `valid_participants`**, vốn là danh sách học viên tham gia.
- Người tạo/phụ trách buổi học (Mentor/Trainer - `meeting.created_by`) không nằm trong vòng lặp này.
- Hệ thống hoàn toàn không kiểm tra xem Mentor đã nộp Đánh giá tổng thể (`MeetingOverallEvaluation`) hay chưa.

### 1.2 Xung đột thời hạn đánh giá 24h vs 72h
- Trong `backend/app/meeting/domain/meeting.py`:
  `meeting.evaluation_deadline` đang tính: `self.end_time + timedelta(hours=24)`.
- Trong khi hệ thống vi phạm (`CheckEvaluationDeadlineJobUseCase` và `specs/038-violation-delay`):
  Thời hạn đánh giá chuẩn là `MEETING_EVALUATION_DEADLINE_HOURS = 72` (72 giờ = 3 ngày).
- Vì thuộc tính domain trả về 24h: Sau 24h, hàm `meeting.is_evaluation_expired(now)` trả về `True` khiến Scanner bỏ qua buổi học, dừng gửi nhắc nhở trước 48h so với hạn phạt thực tế!

---

## 2. Quyết Định Kỹ Thuật (Technical Decisions)

### Quyết định 1: Single Source of Truth cho `evaluation_deadline`
- **Giải pháp**: Nhập hằng số `MEETING_EVALUATION_DEADLINE_HOURS` từ `app.meeting.domain.constants` vào `app.meeting.domain.meeting.py`.
- **Cách tính**:
  ```python
  @property
  def evaluation_deadline(self) -> datetime | None:
      if not self.enable_evaluation:
          return None
      return self.end_time + timedelta(hours=MEETING_EVALUATION_DEADLINE_HOURS)
  ```
- **Lợi ích**: Đồng bộ 100% giữa Domain Entity, Job phạt vi phạm (CheckEvaluationDeadline) và Scanner nhắc nhở (MeetingEvaluationScanner).

### Quyết định 2: Mở rộng `MeetingEvaluationTaskScanner` để quét Mentor
- **Giải pháp**:
  - Inject thêm `overall_eval_repo: MeetingOverallEvaluationRepository` vào constructor của `MeetingEvaluationTaskScanner`.
  - Trong vòng lặp mỗi meeting:
    1. Kiểm tra Mentor (`meeting.created_by`):
       - Nếu `not self.overall_eval_repo.exists_for_meeting(meeting.id)`:
         Sinh candidate nhắc nhở Mentor nộp Đánh giá tổng thể buổi học.
       - Kiểm tra thêm: Các học viên tham gia (`valid_participants`) đã được Mentor đánh giá qua `EvaluationType.TRAINER_TO_TRAINEE` chưa. Nếu còn học viên chưa được đánh giá, sinh candidate nhắc nhở Mentor hoàn thành đánh giá học viên.
    2. Kiểm tra Trainees (`valid_participants`):
       - Giữ nguyên luồng nhắc nhở học viên đánh giá Trainer nếu học viên chưa nộp.

### Quyết định 3: Sửa `action_url` trỏ về route chuẩn của frontend
- **Hiện tại**: `/dashboard/meetings/{meeting.id}/evaluate` (404 Not Found do không có route này).
- **Sửa thành**: `/dashboard/meetings/{meeting.id}` (Trang chi tiết buổi họp có sẵn nút mở modal đánh giá).

### Quyết định 4: Mở rộng cửa sổ tìm kiếm buổi họp
- **Hiện tại**: `three_days_ago = now - timedelta(days=3)`
- **Sửa thành**: `scan_window = now - timedelta(days=5)` để đảm bảo bao trọn tất cả các buổi học kết thúc trong vòng 72h qua.
