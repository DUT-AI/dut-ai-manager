# Research & Technical Decisions: Tối Ưu Hóa Tốc Độ Tải Danh Sách Bài Nộp

## 1. Điểm Nghẽn Hiện Tại & Phân Tích Thực Nghiệm

### Vấn Đề 1: Quét toàn bộ bảng User lên RAM (`get_active_users`)
- **Hiện tại**: `all_active_users = {u.id: u for u in self.user_repo.get_active_users() if u.id is not None}`
- **Bất cập**: Truy vấn toàn bộ bảng `users` trong cơ sở dữ liệu để lấy hàng trăm/hàng nghìn user, mặc dù bài tập chỉ giao cho 23 học viên (`assigned_uids`).
- **Giải pháp**: Viết 1 hàm truy vấn duy nhất tại tầng Repository sử dụng `JOIN`:
  ```sql
  SELECT u.id, u.name, u.avatar_url
  FROM homework_assignees ha
  JOIN users u ON ha.user_id = u.id
  WHERE ha.homework_id = :homework_id AND ha.is_deleted = false AND u.is_deleted = false;
  ```
  -> Giảm tải tài nguyên CPU/RAM, tận dụng chỉ mục B-tree của Database.

### Vấn Đề 2: Gọi HTTP runtime sang Quiz API gây Timeout
- **Hiện tại**: Mỗi lần mở trang `/homeworks/{id}`, backend gọi 3 HTTP request sang Quiz API tuần tự (`await` nối tiếp):
  1. `QuizSubmissionHelper.get_lesson_exercises(...)`
  2. `QuizSubmissionHelper.get_coding_completed_map(...)`
  3. `QuizSubmissionHelper.get_game_completed_map(...)`
- **Bất cập**:
  - Bài tập ID 72 không có Game (`requires_game = False`) nhưng vẫn gọi endpoint Game của Quiz API dẫn đến `ReadTimeout (5.0s)`.
  - 3 request tuần tự: Nếu Quiz API bị nghẽn, tổng thời gian bị cộng dồn lên 10-15 giây.
- **Giải pháp**:
  - **DB-First hoàn toàn cho luồng xem**: Giống như trang `/my-homeworks` (Spec 013), toàn bộ bài nộp đã được lưu trữ trong bảng `homework_submissions`. Tầng Use Case đọc trực tiếp từ DB.
  - Cấu trúc các bài tập con (`ExerciseSummaryDTO`) được tổng hợp tự động từ danh sách bản ghi nộp bài trong DB (`db_submissions` đã có sẵn `exercise_id` và `exercise_title`).
  - Nút **"Đồng bộ từ Quiz" (`POST /sync`)** đã có sẵn trên giao diện để người dùng kích hoạt đồng bộ khi cần, loại bỏ hoàn toàn việc gọi Quiz API runtime trong `GET /submission-status`.

## 2. Quyết Định Kỹ Thuật (Decisions & Trade-offs)

| Vấn đề | Quyết định | Lý do & Lợi ích |
|--------|-----------|-----------------|
| Nạp thông tin học viên | Viết `get_assignees_with_user_info(homework_id)` trong `HomeworkRepository` | 1 câu SQL JOIN duy nhất, O(1) database roundtrip |
| Danh sách bài con | Trích xuất từ `db_submissions` nội bộ | Không cần chờ gọi `GET /api/v1/lessons/{slug}/exercises` của Quiz |
| Đồng bộ dữ liệu mới | Sử dụng nút Sync thủ công (`POST /sync`) + Webhook | Phân tách rạch ròi giữa Read path (siêu nhanh) và Sync path (bất đồng bộ) |
| Bảo toàn hợp đồng API | Giữ nguyên 100% schema DTO `HomeworkSubmissionStatusResponse` | Frontend không phải thay đổi, không phát sinh lỗi tương thích |
