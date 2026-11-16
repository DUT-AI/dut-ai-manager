# Quickstart: In-Memory Fake Test Migration Verification

**Feature**: `072-homework-inmemory-test-migration`  
**Date**: 2026-11-16  

---

## 1. Prerequisites
- Virtualenv tại `backend/.venv`
- Toàn bộ dependencies đã cài đặt

---

## 2. Validation Scenarios

### Scenario 1: Checker Test Suite Verification (Zero-Mock)
Chạy bộ test kiểm tra quá hạn bài tập sau khi chuyển đổi sang In-Memory:

```bash
backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py -v
```
**Expected Outcome**: 100% tests PASS, thời gian chạy < 0.2s, 0 mock repository.

---

### Scenario 2: Validation & SSOT Suites Verification
Chạy bộ test tạo/sửa bài tập và phân giải bài tập con:

```bash
backend/.venv/bin/pytest backend/tests/unit/test_homework_validation.py backend/tests/unit/test_homework_ssot.py backend/tests/unit/test_homework_scanner.py -v
```
**Expected Outcome**: 100% tests PASS, lưu và truy vấn thực tế từ RAM.

---

### Scenario 3: Verify Zero-Mock on All Homework Unit Tests
Quét toàn bộ thư mục unit test của homework để kiểm tra không còn import `MagicMock` cho repositories:

```bash
# Kiểm tra không còn MagicMock nào cho Homework repositories
grep -rn "MagicMock" backend/tests/unit/test_homework_*.py | grep -E "repo|Repo"
```
**Expected Outcome**: 0 kết quả phù hợp (không còn mock repository).

---

### Scenario 4: Full System Regression Run
Chạy toàn bộ test suites của hệ thống:

```bash
backend/.venv/bin/pytest backend/tests/ -q
```
**Expected Outcome**: 467/467 tests PASS, không có lỗi hồi quy.
