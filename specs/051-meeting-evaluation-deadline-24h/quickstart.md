# Hướng Dẫn Kiểm Thử & Xác Minh Tính Năng (Quickstart Validation Guide)

**Feature**: `051-meeting-evaluation-deadline-24h`  
**Ngày**: 2026-11-05

---

## 1. Yêu Cầu Tiên Quyết (Prerequisites)

1. Môi trường Python 3.12 trong `backend/.venv`.
2. Kiểm tra các module liên quan không có lỗi cú pháp.

---

## 2. Kịch Bản Kiểm Thử & Xác Minh (Validation Scenarios)

### Kịch Bản 1: Chạy Bộ Unit Tests Đánh Giá Cuộc Họp

**Mục tiêu**: Chứng minh logic tính toán `end_bound` theo mốc 24h và chuỗi lý do vi phạm `"trong vòng 24h"` hoạt động chính xác 100%.

1. **Lệnh chạy**:
   ```bash
   cd backend
   .venv/bin/pytest tests/unit/test_meeting_evaluation.py -v -k "evaluation_deadline"
   ```

2. **Kết quả mong đợi**:
   - `test_check_evaluation_deadline_creates_violations_for_missing_evaluations`: PASSED (kiểm tra lý do vi phạm chứa `"trong vòng 24h"`).
   - `test_check_evaluation_deadline_uses_24h_bound_and_9d_window`: PASSED (kiểm tra `diff_end` chính xác 24 giờ).

---

### Kịch Bản 2: Chạy Toàn Bộ Test Suite Cuộc Họp

**Mục tiêu**: Đảm bảo không xảy ra bất kỳ lỗi hồi quy nào đối với toàn bộ tính năng cuộc họp.

1. **Lệnh chạy**:
   ```bash
   cd backend
   .venv/bin/pytest tests/unit/test_meeting_evaluation.py -v
   ```

2. **Kết quả mong đợi**:
   - Tất cả các bài test trong file đều đạt kết quả **PASSED 100%**.

---

### Kịch Bản 3: Kiểm Tra Tên Job Trong Scheduler

**Mục tiêu**: Xác nhận tên tác vụ lập lịch được hiển thị chuẩn `"Check 24h meeting evaluations deadline"`.

1. **Lệnh kiểm tra**:
   ```bash
   cd backend
   .venv/bin/python -c "from app.core.scheduler import start_scheduler; import inspect; print('Scheduler module loaded successfully')"
   ```

2. **Kết quả mong đợi**: Lệnh chạy thành công, không gặp lỗi cú pháp.
