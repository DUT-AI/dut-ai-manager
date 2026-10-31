# Quickstart Guide: Kiểm Thử Nhắc Nhở Mentor Đánh Giá Buổi Học

**Feature**: `042-mentor-meeting-eval-reminder`  
**Date**: 2026-11-01  

---

## 1. Mục Tiêu Kiểm Thử
Xác nhận rằng khi buổi học kết thúc và bật đánh giá, Mentor (`meeting.created_by`) sẽ nhận được thông báo nhắc nhở nộp đánh giá tổng thể và đánh giá học viên trước thời hạn 72h.

---

## 2. Kịch Bản Kiểm Thử Độc Lập

### Kịch bản 1: Mentor chưa nộp Đánh giá tổng thể
1. **Thiết lập**:
   - Tạo meeting: `id=501`, `title="Python Workshop"`, `created_by=10` (Mentor), `enable_evaluation=True`, kết thúc cách đây 23 giờ (`evaluation_deadline` còn ~49h nữa -> Khớp `ReminderStage.OFFSET_2D`).
   - `overall_eval_repo.exists_for_meeting(501)` trả về `False`.
2. **Hành động**:
   - Gọi `scanner.scan_pending_tasks(now)`.
3. **Kỳ vọng**:
   - Trả về candidate có:
     - `task_type`: `TaskType.MEETING_EVALUATION`
     - `task_id`: `501`
     - `user_id`: `10` (Mentor)
     - `action_url`: `/dashboard/meetings/501`
     - `task_title`: `Đánh giá tổng thể buổi học: Python Workshop`

### Kịch bản 2: Mentor đã nộp Đánh giá tổng thể nhưng chưa đánh giá Trainees
1. **Thiết lập**:
   - Meeting có 2 học sinh tham gia (`user_id=21, 22`).
   - `overall_eval_repo.exists_for_meeting(501)` trả về `True`.
   - Mentor mới chỉ đánh giá học sinh 21 (`TRAINER_TO_TRAINEE`), học sinh 22 chưa được đánh giá.
2. **Hành động**:
   - Gọi `scanner.scan_pending_tasks(now)`.
3. **Kỳ vọng**:
   - Trả về candidate nhắc Mentor hoàn tất đánh giá học viên cho buổi học `501`.

### Kịch bản 3: Hạn chót đánh giá chuẩn 72h
1. **Thiết lập**:
   - Buổi học kết thúc lúc `2026-11-01T10:00:00Z`.
2. **Hành động**:
   - Kiểm tra `meeting.evaluation_deadline`.
3. **Kỳ vọng**:
   - Trả về chính xác `2026-11-04T10:00:00Z` (+72 giờ).
   - `meeting.is_evaluation_expired(now)` trả về `False` khi thời gian hiện tại mới trôi qua 30 giờ (trước đây bị lỗi `True` sau 24h).
