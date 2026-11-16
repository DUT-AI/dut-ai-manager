# Quickstart: Homework Constitution Hardening Validation

**Feature**: `070-homework-constitution-hardening`  
**Date**: 2026-11-16  

---

## 1. Prerequisites
- Python 3.12+ và virtualenv tại `backend/.venv`
- Backend dependencies đã cài đặt (`uv sync` hoặc `pip install -r requirements.txt`)

---

## 2. Validation Scenarios

### Scenario 1: Linter & Static Code Analysis Verification
Kiểm tra toàn bộ mã nguồn module `backend/app/homework` tuân thủ chuẩn tĩnh, không có lỗi C901 hoặc F401/I001.

```bash
# Chạy Ruff linter kiểm tra cú pháp và độ phức tạp cyclomatic (C901)
backend/.venv/bin/ruff check backend/app/homework
```
**Expected Outcome**: Output báo `All checks passed!` với 0 errors / 0 warnings.

---

### Scenario 2: Unit Test Suite Verification
Xác minh toàn bộ các test cases cho domain Homework (bao gồm cả DTO parsing, repository, use cases) hoạt động chuẩn xác và không có regression.

```bash
# Chạy toàn bộ unit tests liên quan đến homework
backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py -v
```
**Expected Outcome**: 100% tests PASS (không có test nào failed hoặc xfailed).

---

### Scenario 3: Integration Test Suite Verification
Xác minh tích hợp giữa Homework và Quiz API client.

```bash
# Chạy integration tests cho Homework Quiz Integration
backend/.venv/bin/pytest backend/tests/integration/test_homework_quiz_integration.py -v
```
**Expected Outcome**: 9/9 integration tests PASS.

---

### Scenario 4: Webhook Contract E2E Verification
Gửi thử nghiệm một webhook submission payload tới backend server để xác minh định dạng trả về chuẩn `ApiResponse[HomeworkWebhookResponse]`.

```bash
# Giả lập payload nộp bài CODING hợp lệ
curl -X POST http://127.0.0.1:8000/api/v1/homeworks/webhook/submission \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $QUIZ_WEBHOOK_SECRET" \
  -d '{
    "lesson_slug": "test-slug",
    "user_id": 1,
    "type": "CODING",
    "submitted_at": "2026-11-16T10:00:00Z",
    "is_passed": true,
    "exercise_id": "ex-01",
    "details": {
      "language": "python",
      "code": "print(1)"
    }
  }'
```
**Expected Outcome**: Trả về HTTP 200 OK với body JSON chứa cấu trúc `ApiResponse[HomeworkWebhookResponse]` theo đúng [homework_webhook_contract.md](contracts/homework_webhook_contract.md).
