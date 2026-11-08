# Research: Khảo sát chi tiết Metadata của Bài nộp Coding và Game

**Feature**: `056-standardize-submission-metadata`  
**Date**: 2026-11-08

---

## 1. Dữ liệu thực tế của Bài nộp CODING

### Nguồn phát sinh
1. **Webhook từ Quiz**: Khi học viên submit mã nguồn (ví dụ bài tập Python, C++...).
2. **Sync từ Quiz**: API `get_homework_submissions_for_sync(slug)`.

### Thuộc tính Metadata trích xuất được từ `details`:
- `original_filename` (string | null): Tên tệp tin gốc mà học viên đã upload (ví dụ: `bai1.py`, `main.cpp`).
- `submission_id` (string | null): ID của lần submit bên hệ thống Quiz.
- `status` (string | null): Trạng thái (ví dụ: `"AC"`, `"WA"`, `"PASSED"`, `"FAILED"`).
- `score` (float | null): Điểm số của bài tập con.
- `attempt_number` (int): Số thứ tự lần nộp của bài con đó.
- `score_details` (list | null): Danh sách chi tiết chấm từng test case (input, expected output, actual output, status).
- `source` (string): `"webhook"` hoặc `"manual_sync"`.

---

## 2. Dữ liệu thực tế của Bài nộp GAME QUIZ

### Nguồn phát sinh
1. **Webhook từ Quiz**: Khi học viên hoàn thành một phiên chơi Game trắc nghiệm.
2. **Sync từ Quiz**: API `get_game_sessions_for_sync(slug)`.

### Thuộc tính Metadata trích xuất được từ `details`:
- `session_id` (string | null): Mã định danh phiên chơi game.
- `final_score` (float | null): Điểm số đạt được trong phiên chơi game (thang điểm 10 hoặc 100).
- `gold` (int): Điểm thưởng hoặc số vàng game tích lũy được trong phiên chơi.
- `total_questions` (int): Tổng số câu hỏi trắc nghiệm của bài game.
- `correct_count` (int): Số câu trả lời chính xác.
- `attempt_count` (int): Số lần học viên đã chơi game này.
- `source` (string): `"webhook"` hoặc `"manual_sync"`.

---

## 3. Quyết định Thiết kế (Design Decisions)

1. **Giữ nguyên trường `details: dict[str, Any]` để đảm bảo tương thích ngược tuyệt đối (Backward Compatibility)**:
   - Các hệ thống hiện tại hoặc client cũ đọc `details` sẽ không bị lỗi.
2. **Bổ sung hai trường strongly-typed trên `HomeworkSubmissionDetailResponse`**:
   - `coding_details: CodingSubmissionDetails | None = None`
   - `game_details: GameSubmissionDetails | None = None`
   - DTO có `@model_validator(mode="before")` tự động ánh xạ:
     - Nếu `submission_type == "CODING"`, parse `details` thành `coding_details`.
     - Nếu `submission_type == "GAME"`, parse `details` thành `game_details`.
3. **Đồng bộ cột `score` trong DB**:
   - Đảm bảo khi tạo hoặc update Game submission, `score` ở cột DB luôn nhận giá trị từ `final_score` nếu `score` ban đầu là None.
