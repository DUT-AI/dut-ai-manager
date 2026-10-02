# Phase 0 Technical Research & Architecture Decisions

## Decision 1: Cấu trúc Mô hình Lưu trữ Đánh giá (Single Table vs Multi-table)

- **Quyết định**: Sử dụng **1 bảng tập trung `meeting_evaluations`** kết hợp với trường `evaluation_type` (`TRAINER_TO_TRAINEE` hoặc `TRAINEE_TO_MEETING`) và lưu điểm chi tiết theo tiêu chí dưới dạng `JSONB` (hoặc bảng chi tiết items/cột có cấu trúc).
- **Lý do**:
  - Tiêu chí đánh giá cố định 4 mục chuẩn hóa cho mỗi chiều nhưng lưu dưới dạng điểm danh sách (`scores: [{"criteria_code": "...", "score": 5}]`) giúp linh hoạt truy vấn, tính trung bình (`average_score`) và tổng hợp thống kê.
  - Tận dụng PostgreSQL JSONB để lưu trữ chi tiết điểm các tiêu chí mà không làm phức tạp hóa quan hệ bảng.
  - Hỗ trợ cờ `is_anonymous` trực tiếp trên bản ghi.
- **Phương án khác đã xem xét**:
  - *2 bảng riêng biệt (`trainer_evaluations` và `trainee_evaluations`)*: Gây trùng lặp mã nguồn repositories, use case logic và khó tái sử dụng component tính toán điểm trung bình.

---

## Decision 2: Xử lý Quyền Riêng Tư và Tính Ẩn Danh (`is_anonymous`)

- **Quyết định**:
  - Tại tầng cơ sở dữ liệu (`infrastructure`), vẫn ghi nhận `reviewer_id` của Trainee để đảm bảo ràng buộc duy nhất (mỗi học viên chỉ nộp 1 lần và phục vụ tác vụ kiểm tra hạn chót 24h).
  - Tại tầng ứng dụng (`application` / `presentation`), khi trả về danh sách nhận xét cho Trainer/Admin, hệ thống sẽ lọc bỏ `reviewer_id` và thông tin User nếu `is_anonymous = True`, thay thế bằng nhãn "Học viên ẩn danh".
- **Lý do**: Đảm bảo tính trung thực trong thống kê hệ thống mà không làm lộ danh tính người đánh giá trên giao diện người dùng.

---

## Decision 3: Cơ chế Xử lý Hạn chót 24h và Tạo Vi phạm Tự động (`Violation`)

- **Quyết định**:
  - Xây dựng use case `check_evaluation_deadline_job_use_case.py`.
  - Tích hợp vào hệ thống scheduler định kỳ chạy mỗi giờ (hoặc quét các buổi học kết thúc cách đây $\ge 24h$ có `enable_evaluation = true`).
  - Đối với Trainee: Kiểm tra trong bảng `meeting_participants` những người có status `JOINED` hoặc `COMPLETED` mà chưa có bản ghi đánh giá tương ứng trong `meeting_evaluations` $\rightarrow$ tạo `Violation` với lý do: *"Chưa hoàn thành đánh giá buổi học [Tên buổi học] trong vòng 24h"*.
  - Đối với Trainer: Kiểm tra nếu số lượng Trainee được đánh giá $< total\_joined\_trainees \rightarrow$ tạo `Violation` cho Trainer với lý do: *"Chưa hoàn tất đánh giá học viên cho buổi học [Tên buổi học] trong vòng 24h"*.
  - Sử dụng cờ hoặc idempotency key để tránh việc quét nhiều lần tạo trùng lặp vi phạm cho cùng một buổi học.

---

## Decision 4: Bộ Tiêu chí Chuẩn hóa Hệ thống (System Defaults)

### A. Chiều 1: Trainer đánh giá Trainee (`TRAINER_TO_TRAINEE`)
1. `ATTENDANCE_CONDUCT` - **Chuyên cần & Tác phong**: Đúng giờ, tuân thủ nội quy lớp học.
2. `INTERACTION_CONTRIBUTION` - **Mức độ Tương tác & Đóng góp**: Phát biểu, đặt câu hỏi, thảo luận sôi nổi.
3. `ABSORPTION_COMPREHENSION` - **Mức độ Tiếp thu & Hiểu bài**: Nắm bắt kiến thức cốt lõi truyền đạt trong buổi học.
4. `PRE_CLASS_PREPARATION` - **Mức độ Chuẩn bị bài trước buổi học**: Đọc trước tài liệu, chuẩn bị bài tập/môi trường trước khi lên lớp.

### B. Chiều 2: Trainee đánh giá Buổi học / Trainer (`TRAINEE_TO_MEETING`)
1. `CONTENT_QUALITY` - **Chất lượng Nội dung bài học**: Rõ ràng, thực tế, bố cục hợp lý.
2. `TEACHING_METHOD` - **Phương pháp Giảng dạy & Hỗ trợ**: Truyền đạt dễ hiểu, giải đáp nhiệt tình.
3. `CLASS_ATMOSPHERE` - **Không khí Lớp học & Sự tương tác**: Lôi cuốn, tạo cảm hứng và động lực.
4. `PRACTICAL_VALUE` - **Giá trị Thu nhận & Tính ứng dụng**: Kiến thức thu nhận bổ ích, có thể ứng dụng ngay.
