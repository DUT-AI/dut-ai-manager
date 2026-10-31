# Research & Technical Decisions: Làm Mới Metadata Bài Tập Khi Đồng Bộ Từ Quiz

**Feature**: `041-sync-homework-refresh-metadata`  
**Date**: 2026-11-01  
**Status**: Completed  

---

## 1. Nghiên cứu & Quyết định Kỹ thuật

### Quyết định 1: Vị trí và thời điểm làm mới Metadata trong luồng `SyncHomeworkFromQuizUseCase`
- **Bối cảnh**: Hiện tại `SyncHomeworkFromQuizUseCase.execute(homework_id)` chỉ kéo danh sách bài nộp của coding (`get_homework_submissions_for_sync`) và game (`get_game_sessions_for_sync`). Nếu giảng viên thêm bài tập con mới trên Quiz mà chưa ai nộp, hoặc vừa bật thêm tính năng Game trên Quiz, hệ thống Manage không hề biết vì không hề gọi API kiểm tra metadata của bài học.
- **Quyết định**:
  - Đặt bước gọi `quiz_api.get_lesson_metadata(slug)` và `quiz_api.get_lesson_exercises(slug)` ngay **ở đầu hàm `execute()`**, trước khi tiến hành kéo bài nộp.
  - Sử dụng kết quả metadata mới nhất để xác định phạm vi cần đồng bộ:
    - Nếu Quiz báo `has_coding=True` mà trước đó `homework.requires_coding=False`, cập nhật thành `True` và lập tức đồng bộ bài nộp coding.
    - Nếu Quiz báo `has_game=True` mà trước đó `homework.requires_game=False`, cập nhật thành `True` và lập tức đồng bộ game sessions.
  - Lưu cấu hình cập nhật vào DB qua `self.homework_repo.save(updated_homework)`.
- **Lý do chọn**: Giúp bài tập trong hệ thống Manage luôn đồng bộ 100% với cấu hình thực tế trên Quiz, không yêu cầu giảng viên phải sửa bài tập thủ công rồi mới bấm đồng bộ.
- **Các giải pháp thay thế đã xem xét**:
  - *Chỉ gọi metadata khi có lỗi*: Không giải quyết được trường hợp bài tập con mới chưa ai nộp (vì không có lỗi xảy ra).
  - *Tạo use case riêng cho việc sync metadata*: Bắt giảng viên phải bấm 2 nút khác nhau (Sync Metadata và Sync Submissions) -> trải nghiệm người dùng kém (poor UX). Bấm 1 nút "Đồng bộ từ Quiz" làm trọn vẹn cả hai là tối ưu nhất.

---

### Quyết định 2: Chiến lược xử lý khi Quiz API lỗi mạng hoặc Timeout
- **Bối cảnh**: `get_lesson_metadata` và `get_lesson_exercises` là các cuộc gọi mạng bên ngoài. Nếu Quiz API bị chập chờn, mạng lag hoặc timeout, quy trình có nên dừng lại hay không?
- **Quyết định**:
  - Áp dụng nguyên tắc **Graceful Degradation (Fail-Safe)**:
    - Bọc cuộc gọi `get_lesson_metadata` và `get_lesson_exercises` trong khối `try/except`.
    - Nếu thành công: Cập nhật metadata mới nhất vào `homework` và lưu DB.
    - Nếu gặp lỗi mạng: Ghi log warning (`logger.warning(...)`) và tiếp tục sử dụng cấu hình hiện có của bài tập (`homework.requires_coding`, `homework.requires_game`) để đồng bộ các bài nộp đã có.
- **Lý do chọn**: Đảm bảo nghiệp vụ đồng bộ bài nộp không bị tê liệt hoàn toàn nếu Quiz API chỉ gặp sự cố tạm thời ở endpoint metadata.

---

### Quyết định 3: Cấu trúc thông tin phản hồi (Response Feedback) cho Quản trị viên
- **Bối cảnh**: Hiện tại endpoint trả về:
  ```python
  {
      "homework_id": homework.id,
      "title": homework.title,
      "synced_coding_count": synced_coding,
      "updated_coding_count": updated_coding,
      "synced_game_count": synced_game,
      "updated_game_count": updated_game,
      "message": "...",
  }
  ```
  Quản trị viên không biết hiện tại Quiz đang có tổng cộng bao nhiêu bài tập con, bao nhiêu câu hỏi game.
- **Quyết định**:
  Bổ sung vào response dictionary các trường rõ ràng:
  - `coding_exercises_count`: Tổng số bài tập coding con hiện có trên Quiz.
  - `game_questions_count`: Tổng số câu hỏi game hiện có trên Quiz.
  - `requires_coding`: Trạng thái yêu cầu coding sau khi đồng bộ.
  - `requires_game`: Trạng thái yêu cầu game sau khi đồng bộ.
  - Cập nhật chuỗi thông điệp `message` phản ánh rõ cả việc cập nhật metadata bài tập con mới lẫn số lượng bài nộp.
