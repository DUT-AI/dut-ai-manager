# Quickstart & Verification Guide: Làm Mới Metadata Khi Đồng Bộ Bài Tập

Tài liệu hướng dẫn kiểm thử và thẩm định tính năng làm mới metadata bài tập con từ Quiz API.

---

## 1. Kịch bản kiểm thử 1: Bài tập con mới chưa ai nộp
**Mục tiêu**: Giảng viên thêm bài tập con mới trên Quiz, chưa có học viên nào nộp bài.

1. Khởi tạo một bài tập trong hệ thống với slug `cnn-basics`, yêu cầu `requires_coding=True`.
2. Mock Quiz API:
   - `get_lesson_metadata("cnn-basics")` trả về: `{"has_coding": True, "coding_count": 2, "has_game": False, "game_question_count": 0}`.
   - `get_lesson_exercises("cnn-basics")` trả về 2 bài tập: `ex-1` và `ex-2` (bài mới).
   - `get_homework_submissions_for_sync("cnn-basics")` trả về danh sách rỗng `[]` (chưa ai nộp).
3. Gọi `SyncHomeworkFromQuizUseCase.execute(homework_id)`.
4. Kết quả mong đợi:
   - Response trả về `coding_exercises_count = 2`.
   - Message thông báo nhận diện thành công 2 bài tập coding.
   - Màn hình nộp bài `GetHomeworkSubmissionStatusUseCase` hiển thị đầy đủ cả `ex-1` và `ex-2` trong danh sách các bài tập con cần làm.

---

## 2. Kịch bản kiểm thử 2: Quiz bổ sung thêm Game trắc nghiệm
**Mục tiêu**: Bài tập ban đầu chỉ có Coding (`requires_game=False`). Giảng viên thêm phần Game Quiz trên hệ thống Quiz.

1. Khởi tạo bài tập với `requires_coding=True`, `requires_game=False`.
2. Mock Quiz API:
   - `get_lesson_metadata` trả về: `has_coding=True, has_game=True, game_question_count=10`.
   - `get_game_sessions_for_sync` trả về 1 session hoàn thành của học sinh A.
3. Gọi `SyncHomeworkFromQuizUseCase.execute(homework_id)`.
4. Kết quả mong đợi:
   - `HomeworkModel.requires_game` trong DB tự động được cập nhật thành `True`.
   - Response trả về `requires_game=True`, `game_questions_count=10`, `synced_game_count=1`.
   - Học sinh A có lượt nộp Game được lưu vào bảng `homework_submissions`.

---

## 3. Lệnh chạy kiểm thử tự động
```bash
backend/.venv/bin/pytest backend/tests/integration/test_homework_quiz_integration.py -k "sync"
backend/.venv/bin/ruff check backend/app/homework/application/sync_homework_use_case.py
```
