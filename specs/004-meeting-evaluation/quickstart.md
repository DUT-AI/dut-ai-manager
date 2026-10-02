# Quickstart & Validation Guide: Meeting Evaluation

Tài liệu hướng dẫn kiểm thử và xác thực luồng tính năng Đánh giá 2 Chiều Buổi học.

---

## 1. Chuẩn bị Môi trường & Dữ liệu Kiểm thử

### A. Chạy Backend & Frontend:
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate # hoặc conda
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### B. Dữ liệu Giả định:
- **Trainer User**: `id: 1` (Role: ADMIN / TRAINER)
- **Trainee 1 User**: `id: 2` (Role: MEMBER, đã tham gia meeting)
- **Trainee 2 User**: `id: 3` (Role: MEMBER, đã tham gia meeting)

---

## 2. Kịch bản Kiểm thử End-to-End

### Kịch bản 1: Tạo buổi học có bật Đánh giá 2 chiều
1. Trainer gửi request `POST /api/v1/meetings/` với payload:
   ```json
   {
     "title": "Lớp đào tạo Clean Architecture",
     "start_time": "2026-10-02T14:00:00",
     "end_time": "2026-10-02T16:00:00",
     "require_check_in": true,
     "enable_evaluation": true,
     "user_ids": [2, 3]
   }
   ```
2. **Kỳ vọng**: Buổi học được tạo với `enable_evaluation: true`, hạn chót đánh giá là `2026-10-03T16:00:00` (sau 24h).

---

### Kịch bản 2: Trainer đánh giá Trainee theo 4 tiêu chí
1. Sau khi buổi học kết thúc, Trainer gửi request `POST /api/v1/meetings/1/evaluations/trainer`:
   ```json
   {
     "target_user_id": 2,
     "scores": [
       { "criteria_code": "ATTENDANCE_CONDUCT", "score": 5 },
       { "criteria_code": "INTERACTION_CONTRIBUTION", "score": 4 },
       { "criteria_code": "ABSORPTION_COMPREHENSION", "score": 5 },
       { "criteria_code": "PRE_CLASS_PREPARATION", "score": 5 }
     ],
     "feedback_text": "Em chuẩn bị bài trước rất tốt và chủ động đặt câu hỏi."
   }
   ```
2. **Kỳ vọng**: Trả về HTTP 200, điểm trung bình được tính là `4.75`, trạng thái Trainee 2 chuyển sang "Đã đánh giá".

---

### Kịch bản 3: Trainee gửi đánh giá Ẩn danh về Buổi học
1. Trainee 1 (user_id 2) gửi request `POST /api/v1/meetings/1/evaluations/trainee`:
   ```json
   {
     "is_anonymous": true,
     "scores": [
       { "criteria_code": "CONTENT_QUALITY", "score": 5 },
       { "criteria_code": "TEACHING_METHOD", "score": 5 },
       { "criteria_code": "CLASS_ATMOSPHERE", "score": 4 },
       { "criteria_code": "PRACTICAL_VALUE", "score": 5 }
     ],
     "feedback_text": "Buổi học rất bổ ích, mong có thêm bài tập mẫu."
   }
   ```
2. **Kỳ vọng**: Trả về HTTP 200. Khi Trainer gọi API `GET /api/v1/meetings/1/evaluations/summary`, nhận xét hiển thị dưới tên "Học viên ẩn danh". Trainee 1 được mở khóa quyền xem kết quả đánh giá từ Trainer.

---

### Kịch bản 4: Tự động tạo Vi phạm (`Violation`) sau 24h
1. Trainee 2 (user_id 3) không thực hiện đánh giá lớp học trong vòng 24h.
2. Kích hoạt tác vụ quét deadline `check_evaluation_deadline_job_use_case`.
3. **Kỳ vọng**: Hệ thống tự động tạo 01 bản ghi `Violation` cho user 3 với lý do: `"Chưa hoàn thành đánh giá buổi học Lớp đào tạo Clean Architecture trong vòng 24h"`.
