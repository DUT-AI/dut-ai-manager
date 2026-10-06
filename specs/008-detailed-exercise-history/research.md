# Research & Technical Decisions: Quản Lý Và Lưu Vết Chi Tiết Lịch Sử Từng Bài Tập Coding

**Feature**: `008-detailed-exercise-history`  
**Date**: 2026-10-06  
**Status**: Completed

---

## 1. Vấn Đề Cốt Lõi & Mục Tiêu

Hệ thống quản lý bài tập hiện tại gặp phải bài toán lệch mô hình giữa hai ứng dụng:
- **DUT-AI Quiz**: Một `Lesson` có thể chứa $N$ bài tập coding (`HomeworkEntity` gắn với `lesson_id`).
- **DUT-AI Manager**: Quản lý ở cấp `Lesson` (`slug`), nhận webhook và đồng bộ trạng thái nộp bài chung cho toàn bộ lesson. Khi học viên nộp 1 bài bất kỳ, hệ thống đã ghi nhận hoàn thành cả lesson.

**Mục tiêu nghiên cứu**:
1. Thiết kế cơ chế trao đổi dữ liệu chi tiết từng bài tập con (`exercise_id`) giữa Quiz và Manager.
2. Thiết kế mô hình lưu trữ lịch sử nộp bài con trên Manager.
3. Chuẩn hóa bộ Pydantic Models 2 chiều cho Webhook, Sync API và Status API.
4. Đảm bảo tính nhất quán (Idempotency, Data Consistency, Zero Regression).

---

## 2. Các Quyết Định Kỹ Thuật (Decisions & Rationale)

### Quyết Định 1: Định danh bài tập coding con (Exercise Identity)

- **Quyết định**: 
  - Phía Quiz: Mỗi bài tập coding vốn có khóa chính `id: UUID` trong bảng `homeworks` của Quiz. Khi giao tiếp với Manager, Quiz sẽ gửi trường `exercise_id` (chuỗi UUID) kèm `exercise_title` (tên bài tập).
  - Phía Manager: Bổ sung trường `exercise_id: String(64)` và `exercise_title: String(255)` vào bảng `homework_submissions`. Trường này là `nullable=True` để tương thích ngược với bài nộp Game và các bài nộp cũ.
- **Lý do chọn**: 
  - Tận dụng trực tiếp UUID sẵn có từ Quiz mà không cần tạo bảng mới phức tạp bên Manager.
  - Tiết kiệm chi phí vận hành: Manager không cần đồng bộ trước toàn bộ catalog bài tập con vào database riêng, mà nạp dynamic qua API và lưu vết trực tiếp trong submission log.
- **Phương án khác đã xem xét**:
  - *Tạo bảng `homework_exercises` riêng trong Manager*: Bị từ chối vì làm tăng độ phức tạp khi Quiz chỉnh sửa/xóa bài tập con; Manager chỉ là bên giám sát (Observability/Tracking), việc lưu `exercise_id` trong submission log và fetch exercise metadata theo nhu cầu giúp hệ thống linh hoạt hơn.

---

### Quyết Định 2: Chiến lược Idempotent Upsert cho bài nộp con

- **Quyết định**:
  - Khóa logic xác định bản ghi bài nộp:
    * Đối với **CODING**: Cặp `(homework_id, user_id, exercise_id)`.
    * Đối với **GAME**: Cặp `(homework_id, user_id, submission_type="GAME")`.
  - Khi nhận webhook nộp bài hoặc chấm bài mới:
    * Nếu bản ghi `(homework_id, user_id, exercise_id)` chưa tồn tại: Thêm mới (INSERT).
    * Nếu đã tồn tại: Cập nhật (UPDATE) điểm số, trạng thái `is_passed`, thời gian nộp `submitted_at`, số lần nộp `attempt_number`, tên file `original_filename` và `details`.
- **Lý do chọn**:
  - Tránh duplicate dữ liệu khi Quiz gửi lại webhook (retry) hoặc khi học viên nộp lại nhiều lần để cải thiện điểm.
  - Luôn phản ánh chính xác trạng thái và điểm số mới nhất của học viên trên từng bài tập.

---

### Quyết Định 3: Tiêu chuẩn hoàn thành Lesson và API Đồng Bộ

- **Quyết định**:
  - Phía Quiz:
    1. Cung cấp endpoint `GET /api/v1/lessons/{lesson_slug}/exercises` trả về danh sách toàn bộ bài tập coding con đang active của lesson.
    2. Cập nhật endpoint `GET /api/v1/homeworks/{lesson_slug}/completed-members`: Chỉ trả về `user_id` là hoàn thành khi:
       $$\text{COUNT}(\text{DISTINCT } \text{HomeworkSubmission.homework_id}) \ge \text{Total Active Exercises of Lesson}$$
    3. Cập nhật endpoint `GET /api/v1/homeworks/{lesson_slug}/submissions-for-sync`: Bổ sung `exercise_id` (chuỗi UUID), `exercise_title`, `attempt_number`, `score`, `is_pass`.
  - Phía Manager:
    * Khi hiển thị trạng thái (`GetHomeworkSubmissionStatusUseCase`), gọi Quiz API để lấy danh sách bài tập con, kết hợp với các bài nộp trong DB của Manager để dựng ma trận chi tiết:
      - `total_required = len(exercises)`
      - `total_completed = count(passed_exercises)`
      - Phân loại 3 trạng thái: `COMPLETED` ($k = N$), `PARTIALLY_SUBMITTED` ($0 < k < N$), `NOT_SUBMITTED` ($k = 0$).
- **Lý do chọn**:
  - Phản ánh trung thực 100% tình trạng nộp bài của sinh viên, chấm dứt tình trạng nộp 1 bài là pass cả lesson.

---

### Quyết Định 4: Chuẩn hóa Schema & Giao thức truyền tin bằng Pydantic V2

- **Quyết định**:
  - Toàn bộ DTOs trao đổi qua Webhook và REST API đều sử dụng `pydantic.BaseModel` (Pydantic V2) với `ConfigDict` và validation chặt chẽ.
  - Webhook được bảo vệ bằng header `X-Webhook-Secret`.
  - Hỗ trợ chuyển đổi mốc thời gian ISO 8601 sang naive ICT datetime theo quy chuẩn chung của hệ thống Manager (`to_utc7_naive`).
- **Lý do chọn**:
  - Phát hiện lỗi sai kiểu dữ liệu ngay tại tầng đầu vào, ghi log rõ ràng, không làm gián đoạn luồng xử lý chính.

---

## 3. Bảng Tổng Hợp So Sánh Kiến Trúc

| Thành phần | Hiện tại | Thiết kế mới |
| :--- | :--- | :--- |
| **Quiz Webhook** | Chỉ gửi `lesson_slug`, `user_id`, `submission_id` | Gửi thêm `exercise_id`, `exercise_title`, `score`, `attempt_number`, `is_passed` |
| **Quiz /completed-members** | Chỉ cần $\ge 1$ bài nộp là coi hoàn thành | Phải nộp đủ $100\%$ ($N/N$) bài tập coding active |
| **Quiz Sync API** | Trả về submission không có `exercise_id` | Trả về submission kèm `exercise_id`, `exercise_title`, `score`, `is_pass` |
| **Manager Database** | Bảng `homework_submissions` không có `exercise_id` | Bổ sung `exercise_id`, `exercise_title`, `score`, `attempt_number`, composite index |
| **Manager Status API** | Chỉ trả về list `submitted` / `not_submitted` dạng nhị phân | Trả về danh sách bài tập con và tiến độ $k/N$ kèm chi tiết từng bài nộp |
| **Overdue Checker** | Coi là hoàn thành nếu có $\ge 1$ bài nộp | Coi là hoàn thành nếu đã nộp đủ $100\%$ các bài tập con |
