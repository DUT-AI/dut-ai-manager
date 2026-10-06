# Quickstart & Validation Guide: Quản Lý Và Lưu Vết Chi Tiết Lịch Sử Từng Bài Tập Coding

**Feature**: `008-detailed-exercise-history`  
**Date**: 2026-10-06  
**Status**: Ready for Verification

---

## 1. Mục Đích

Tài liệu này cung cấp các kịch bản kiểm thử tự động và thủ công nhằm xác thực tính đúng đắn của việc lưu vết chi tiết từng bài tập coding con của Lesson giữa **DUT-AI Quiz** và **DUT-AI Manager**.

---

## 2. Kịch Bản Xác Thực (Validation Scenarios)

### Scenario 1: Kiểm thử Unit Test & Pydantic Validation

Kiểm tra xem Pydantic Models có bắt lỗi chính xác khi thiếu trường bắt buộc hoặc sai định dạng:

```bash
# Chạy test suite của Manager
pytest tests/test_homework_webhook.py -v
pytest tests/test_homework/ -v
```

### Scenario 2: Mô phỏng Webhook nộp từng bài tập coding con

Gửi request HTTP mô phỏng Webhook từ Quiz sang Manager:

```bash
curl -X POST http://localhost:8000/api/v1/homeworks/webhook/submission \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: ${MANAGE_WEBHOOK_SECRET}" \
  -d '{
    "lesson_slug": "batch-normalization",
    "user_id": 42,
    "type": "CODING",
    "submitted_at": "2026-10-06T14:30:00+07:00",
    "is_passed": true,
    "exercise_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "exercise_title": "Bài tập 1: Cài đặt BatchNorm2d Forward",
    "submission_id": "c8a6b2d1-9f3e-4b77-a8b2-5f8e6c1d4a3e",
    "attempt_number": 1,
    "score": 100.0,
    "original_filename": "forward.py"
  }'
```

**Kết quả kỳ vọng**:
- Status code `200 OK`.
- Response: `{"status": "recorded", "submission_id": <int>, "homework_id": <int>, "user_id": 42}`.
- Database: Bảng `homework_submissions` xuất hiện bản ghi với đúng `exercise_id` và `exercise_title`.

---

### Scenario 3: Xác thực Ma Trận Tiến Độ ($k/N$ Bài Tập)

Gọi API lấy chi tiết trạng thái nộp bài:

```bash
curl -X GET http://localhost:8000/api/v1/homeworks/15/submission-status \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Kết quả kỳ vọng**:
- Phản hồi chứa danh sách `coding_exercises` (tất cả các bài tập con của lesson).
- Học viên chỉ nộp $1/2$ bài được xếp vào nhóm `partially_submitted` hoặc hiển thị rõ `total_coding_completed: 1`, `total_coding_required: 2`.
- Học viên nộp đủ $2/2$ bài được xếp vào nhóm `completed` (`is_fully_completed: true`).

---

### Scenario 4: Kiểm thử Quá Hạn (Overdue Checker)

Chạy tác vụ kiểm tra bài tập quá hạn:

```bash
# Thực thi qua test hoặc use case runner
pytest tests/test_homework/test_check_overdue.py -v
```

**Kết quả kỳ vọng**:
- Học viên nộp thiếu bài khi đã quá deadline bị phát sự kiện `HomeworkOverdueDetected`.
- Học viên nộp đủ $100\%$ các bài con trước deadline không bị tính vi phạm.

---

## 3. Lệnh Kiểm Tra Toàn Diện Hệ Thống (Quality Gates)

```bash
# 1. Typecheck (Zero Diagnostics)
make typecheck

# 2. Toàn bộ Unit & Integration Tests
make test
```
