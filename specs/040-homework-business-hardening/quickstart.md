# Quickstart Validation Guide: Homework Business Hardening

**Feature**: `040-homework-business-hardening`  
**Date**: 2026-10-31  

---

## 1. Mục tiêu kiểm thử End-to-End
Xác thực 3 trụ cột nghiệp vụ được củng cố:
1. `HomeworkTaskScanner` phát hiện chính xác học sinh chưa hoàn thành đủ bài (thiếu Coding hoặc thiếu Game) và tạo ứng viên nhắc nhở.
2. `CheckOverdueHomeworkUseCase` & `GetHomeworkSubmissionStatusUseCase` lấy danh mục bài tập con từ Quiz API thay vì bới submissions cũ.
3. `PostponeStrategy` từ chối các đơn hoãn lùi quá khứ, bài đã quá hạn, bài đã nộp xong; và cho phép hoãn tích luỹ nhiều lần <= 4 ngày.

---

## 2. Các kịch bản kiểm thử tự động (Automated Scenarios)

### Kịch bản 1: Kiểm thử Reminder Scanner với bài tập đa yêu cầu
```bash
backend/.venv/bin/pytest backend/tests/unit/test_reminder_use_cases.py -k "test_homework_scanner"
```
- **Kỳ vọng**: 
  - User mới chỉ nộp Game -> Vẫn nằm trong candidates nhắc nhở.
  - User mới chỉ nộp 1 bài Coding con -> Vẫn nằm trong candidates nhắc nhở.
  - User đã nộp đủ cả Coding và Game -> Được loại trừ khỏi candidates nhắc nhở.

### Kịch bản 2: Kiểm thử Quiz Exercises trong CheckOverdue & SubmissionStatus
```bash
backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py
```
- **Kỳ vọng**:
  - Khi Quiz API trả về 3 bài con, học sinh chỉ nộp 1 bài con thì bị đánh dấu chưa hoàn thành coding.
  - Khi Quiz API không phản hồi, cơ chế fallback từ submission cũ hoạt động mượt mà.

### Kịch bản 3: Kiểm thử Rào chắn & Hoãn tích luỹ trong PostponeStrategy
```bash
backend/.venv/bin/pytest backend/tests/unit/test_permission_strategies.py -k "postpone"
```
- **Kỳ vọng**:
  - Tạo đơn với `extended_deadline` ở quá khứ -> Ném `HTTPException 400: Thời gian gia hạn mới phải ở tương lai`.
  - Tạo đơn khi `current_deadline` đã qua -> Ném `HTTPException 400: Bài tập đã quá hạn, không thể tạo đơn xin hoãn`.
  - Tạo đơn khi bài tập đã làm xong -> Ném `HTTPException 400: Bạn đã hoàn thành bài tập này, không thể xin hoãn`.
  - Tạo đơn lần 2 nối tiếp khi deadline mới <= deadline cũ + 4 ngày -> Chấp thuận thành công.

---

## 3. Lệnh chạy toàn bộ kiểm thử
```bash
backend/.venv/bin/pytest backend/tests/unit backend/tests/integration backend/tests/api/test_homework_api.py
```
- **Kỳ vọng**: 100% tests passed không có lỗi hồi quy.
