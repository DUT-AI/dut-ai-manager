# Phase 0 Technical Research & Architecture Decisions

## Decision 1: Cấu trúc Mô hình Lưu trữ Đánh giá (Tách Biệt Bảng Cho Meeting và Cá Nhân)

- **Quyết định**:
  - Tạo bảng riêng biệt **`meeting_overall_evaluations`** dành cho việc Trainer đánh giá buổi học với quan hệ **1 - 1** với bảng `meetings` (`UNIQUE(meeting_id)`).
  - Duy trì bảng **`meeting_evaluations`** dành riêng cho Trainee đánh giá cá nhân Trainer (`UNIQUE(meeting_id, reviewer_id, target_user_id)`).
  - Điểm chi tiết các tiêu chí lưu dưới dạng `JSONB` (`scores: [{"criteria_code": "...", "score": 5}]`) và điểm trung bình lưu tại cột `average_score` (FLOAT).
- **Lý do**:
  - Tách bạch hoàn toàn giữa việc đánh giá một thực thể sự kiện/buổi học (`Meeting`) và đánh giá một con người/cá nhân (`User`). Khóa ngoại và ràng buộc toàn vẹn dữ liệu chuẩn hóa, không cần dùng nullable foreign keys hoặc các cờ phân loại phức tạp.
  - Đảm bảo quan hệ 1 - 1 nghiêm ngặt: Mỗi meeting chỉ có duy nhất 1 bản ghi đánh giá tổng thể từ Trainer.
- **Phương án khác đã xem xét**:
  - *Gộp chung vào bảng `meeting_evaluations` với `target_user_id = NULL`*: Dễ gây nhầm lẫn trong câu truy vấn, phá vỡ tính đồng nhất của đối tượng nhận đánh giá cá nhân.

---

## Decision 2: Xử lý Quyền Riêng Tư và Tính Ẩn Danh (`is_anonymous`)

- **Quyết định**:
  - Tại tầng cơ sở dữ liệu (`infrastructure`), vẫn ghi nhận `reviewer_id` của Trainee trong `meeting_evaluations` để đảm bảo mỗi Trainee chỉ gửi 1 lần và phục vụ tác vụ kiểm tra hạn chót 24h.
  - Tại tầng ứng dụng (`application` / `presentation`), khi trả về danh sách nhận xét cho Trainer/Admin, hệ thống sẽ ẩn thông tin User nếu `is_anonymous = True`, thay thế bằng nhãn "Học viên ẩn danh".
  - Đánh giá tổng thể meeting của Trainer (`MeetingOverallEvaluation`) được công khai ngay cho mọi Trainee tham gia meeting xem mà không đòi hỏi điều kiện ràng buộc.
- **Lý do**: Đảm bảo tính trung thực trong thống kê hệ thống mà không làm lộ danh tính người đánh giá trên giao diện người dùng.

---

## Decision 3: Cơ chế Xử lý Hạn chót 24h và Tạo Vi phạm Tự động (`Violation`)

- **Quyết định**:
  - Xây dựng use case `check_evaluation_deadline_job_use_case.py`.
  - Tích hợp vào hệ thống scheduler định kỳ chạy mỗi giờ (quét các buổi học kết thúc cách đây $\ge 24h$ có `enable_evaluation = true`).
  - **Đối với Trainer**: Kiểm tra xem đã có bản ghi trong bảng `meeting_overall_evaluations` cho `meeting_id` đó hay chưa. Nếu chưa $\rightarrow$ tự động tạo 01 `Violation` cho Trainer với lý do: *"Chưa hoàn thành đánh giá buổi học [Tên buổi học] trong vòng 24h"*.
  - **Đối với Trainee**: Kiểm tra trong bảng `meeting_participants` những học viên có status `JOINED` hoặc `COMPLETED` mà chưa có bản ghi gửi Trainer trong `meeting_evaluations` $\rightarrow$ tạo 01 `Violation` cho Trainee với lý do: *"Chưa hoàn thành đánh giá Trainer cho buổi học [Tên buổi học] trong vòng 24h"*.
  - Sử dụng idempotency key hoặc cờ kiểm tra tránh tạo trùng lặp vi phạm cho cùng một buổi học.

---

## Decision 4: Bộ Tiêu chí Chuẩn hóa Hệ thống (System Defaults - Giữ Nguyên)

### A. Chiều 1: Trainer đánh giá Tổng thể Buổi học (`MeetingOverallEvaluation`)
1. `ATTENDANCE_CONDUCT` - **Chuyên cần & Tác phong**: Đúng giờ, tuân thủ nội quy lớp học.
2. `INTERACTION_CONTRIBUTION` - **Mức độ Tương tác & Đóng góp**: Phát biểu, đặt câu hỏi, thảo luận sôi nổi.
3. `ABSORPTION_COMPREHENSION` - **Mức độ Tiếp thu & Hiểu bài**: Nắm bắt kiến thức cốt lõi truyền đạt trong buổi học.
4. `PRE_CLASS_PREPARATION` - **Mức độ Chuẩn bị bài trước buổi học**: Đọc trước tài liệu, chuẩn bị bài tập/môi trường trước khi lên lớp.

### B. Chiều 2: Trainee đánh giá Cá nhân Trainer (`MeetingEvaluation`)
1. `CONTENT_QUALITY` - **Chất lượng Nội dung bài học**: Rõ ràng, thực tế, bố cục hợp lý.
2. `TEACHING_METHOD` - **Phương pháp Giảng dạy & Hỗ trợ**: Truyền đạt dễ hiểu, giải đáp nhiệt tình.
3. `CLASS_ATMOSPHERE` - **Không khí Lớp học & Sự tương tác**: Lôi cuốn, tạo cảm hứng và động lực.
4. `PRACTICAL_VALUE` - **Giá trị Thu nhận & Tính ứng dụng**: Kiến thức thu nhận bổ ích, có thể ứng dụng ngay.
