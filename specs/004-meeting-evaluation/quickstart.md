# Quickstart & Validation Guide: Meeting Evaluation

Tài liệu hướng dẫn kiểm thử và xác thực luồng tính năng Đánh giá Buổi học (Trainer đánh giá Meeting 1-1 & Trainee đánh giá cá nhân Trainer).

---

## 1. Chuẩn bị Môi trường & Dữ liệu Kiểm thử

### A. Chạy Backend & Frontend:
```bash
# Terminal 1 - Backend
make backend-dev

# Terminal 2 - Frontend
make frontend-dev
```

### B. Dữ liệu Giả định:
- **Trainer User**: `id: 1` (Role: ADMIN / TRAINER, người tạo meeting)
- **Trainee 1 User**: `id: 2` (Role: MEMBER, đã tham gia meeting)
- **Trainee 2 User**: `id: 3` (Role: MEMBER, đã tham gia meeting)

---

## 2. Kịch bản Kiểm thử End-to-End

### Kịch bản 1: Tạo buổi học có bật Đánh giá
1. Trainer gửi request `POST /api/v1/meetings/` với payload:
   ```json
   {
     "title": "Lớp đào tạo Clean Architecture",
     "start_time": "2026-10-11T14:00:00",
     "end_time": "2026-10-11T16:00:00",
     "require_check_in": true,
     "enable_evaluation": true,
     "user_ids": [2, 3]
   }
   ```
2. **Kỳ vọng**: Buổi học được tạo với `enable_evaluation: true`, hạn chót đánh giá là `2026-10-12T16:00:00` (sau 24h).

---

### Kịch bản 2: Trainer đánh giá tổng thể Buổi học (Quan hệ 1 - 1)
1. Sau khi buổi học kết thúc, Trainer gửi request `POST /api/v1/meetings/1/evaluations/overall`:
   ```json
   {
     "scores": [
       { "criteria_code": "ATTENDANCE_CONDUCT", "score": 5 },
       { "criteria_code": "INTERACTION_CONTRIBUTION", "score": 4 },
       { "criteria_code": "ABSORPTION_COMPREHENSION", "score": 5 },
       { "criteria_code": "PRE_CLASS_PREPARATION", "score": 4 }
     ],
     "general_feedback": "Lớp học tích cực, các bạn chuẩn bị bài và tham gia thảo luận sôi nổi."
   }
   ```
2. **Kỳ vọng**:
   - Trả về HTTP 200, lưu 1 bản ghi vào `meeting_overall_evaluations`.
   - Điểm trung bình được tính là `4.5`.
   - Nếu Trainer thử gửi lần 2, hệ thống trả về HTTP 400 (do ràng buộc `UNIQUE(meeting_id)`).

---

### Kịch bản 3: Trainee xem đánh giá buổi học & Gửi đánh giá Trainer
1. Trainee 1 (user_id 2) gọi `GET /api/v1/meetings/1/evaluations/overall`:
   - **Kỳ vọng**: Xem được ngay điểm số `4.5` và lời nhận xét chung của Trainer mà không bị chặn.
2. Trainee 1 gửi đánh giá ẩn danh cho Trainer: `POST /api/v1/meetings/1/evaluations/trainee`:
   ```json
   {
     "target_user_id": 1,
     "is_anonymous": true,
     "scores": [
       { "criteria_code": "CONTENT_QUALITY", "score": 5 },
       { "criteria_code": "TEACHING_METHOD", "score": 5 },
       { "criteria_code": "CLASS_ATMOSPHERE", "score": 4 },
       { "criteria_code": "PRACTICAL_VALUE", "score": 5 }
     ],
     "feedback_text": "Trainer truyền đạt rất dễ hiểu và hỗ trợ nhiệt tình."
   }
   ```
3. **Kỳ vọng**:
   - Trả về HTTP 200.
   - Khi Trainer gọi `GET /api/v1/meetings/1/evaluations/summary`, nhận xét của Trainee 1 hiển thị dưới tên "Học viên ẩn danh" mà không lộ thông tin cá nhân.

---

### Kịch bản 4: Tự động tạo Vi phạm (`Violation`) sau 24h
1. Giả lập sau 24h:
   - Nếu Trainer chưa gửi `MeetingOverallEvaluation` $\rightarrow$ Tự động tạo 01 `Violation` cho Trainer ("Chưa hoàn thành đánh giá buổi học trong vòng 24h").
   - Nếu Trainee 2 (user_id 3) chưa gửi đánh giá Trainer $\rightarrow$ Tự động tạo 01 `Violation` cho Trainee 2 ("Chưa hoàn thành đánh giá Trainer trong vòng 24h").
