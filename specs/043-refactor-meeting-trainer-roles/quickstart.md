# Quickstart Guide: Kiểm Thử Phân Loại Trainer & Trainee

**Feature**: `043-refactor-meeting-trainer-roles`  
**Date**: 2026-11-01  

---

## 1. Mục Tiêu Kiểm Thử
Xác nhận rằng:
1. Form tạo buổi học lưu chính xác Trainer và Trainee vào bảng `meeting_participants`.
2. Trainer (khác `created_by`) có toàn quyền điểm danh, chỉnh sửa trạng thái và nộp đánh giá trong meeting.
3. Học viên nộp đánh giá cho Trainer thực tế chứ không phải `created_by`.

---

## 2. Các Kịch Bản Kiểm Thử

### Kịch bản 1: Tạo meeting với nhiều Trainer độc lập với Creator
1. **Thiết lập**:
   - User 1 (Admin/Creator) tạo meeting qua API:
     - `trainer_ids = [10, 11]` (Mentor Nam, Mentor Hương)
     - `trainee_ids = [21, 22]` (Học viên An, Bình)
2. **Hành động**:
   - Gọi `create_meeting_use_case.execute(creator_id=1, data=...)`.
3. **Kỳ vọng**:
   - `meeting.created_by == 1`.
   - `meeting.participants` có 4 bản ghi:
     - User 10, 11 có `role == ParticipantRole.TRAINER`.
     - User 21, 22 có `role == ParticipantRole.TRAINEE`.
   - `len(meeting.trainers) == 2`.

### Kịch bản 2: Bất kỳ Trainer nào cũng có toàn quyền quản lý & nộp đánh giá tổng thể
1. **Thiết lập**:
   - User 11 (Mentor Hương) đăng nhập (không phải Admin, không phải người tạo `created_by=1`).
2. **Hành động**:
   - Gửi request `POST /api/v1/meetings/{meeting_id}/overall-evaluation`.
3. **Kỳ vọng**:
   - Vượt qua kiểm tra quyền `check_meeting_evaluation_permission`.
   - Lưu thành công `MeetingOverallEvaluation` với `trainer_id = 11`.

### Kịch bản 3: Trainee đánh giá đúng Trainer mong muốn khi có nhiều Trainer
1. **Thiết lập**:
   - Học sinh 21 tham gia buổi học và nộp đánh giá cho Mentor Nam (User 10).
2. **Hành động**:
   - Gọi `submit_trainee_evaluation_use_case.execute(reviewer_id=21, target_user_id=10, ...)`.
3. **Kỳ vọng**:
   - `target_user_id` lưu đúng User 10 thay vì Admin (User 1).

### Kịch bản 4: Kiểm tra giao diện UI phân tách 2 bảng
1. **Thiết lập**:
   - Mở trang chi tiết meeting (`MeetingParticipantsTab`) hoặc modal danh sách (`ParticipantListModal`).
2. **Kỳ vọng**:
   - Xuất hiện 2 bảng riêng biệt:
     - **Bảng Giảng viên**: Hiển thị 2 Trainer (User 10, 11), trạng thái điểm danh, ảnh quẹt thẻ, điểm đánh giá. Không hiển thị nút chấm điểm học viên.
     - **Bảng Học viên**: Hiển thị 2 Trainee (User 21, 22), trạng thái điểm danh, trạng thái đánh giá, nút điểm danh và nút đánh giá học viên dành cho Trainer.
