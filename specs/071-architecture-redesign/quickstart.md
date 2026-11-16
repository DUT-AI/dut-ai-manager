# Quickstart: Clean Architecture Ports & In-Memory Verification

**Feature**: `071-architecture-redesign`  
**Date**: 2026-11-16  

---

## 1. Prerequisites
- Python 3.12+ và virtualenv tại `backend/.venv`
- Backend dependencies đã cài đặt

---

## 2. Validation Scenarios

### Scenario 1: Port Implementation Contract Test
Kiểm tra cả hai adapter (`SQLAlchemy` và `InMemory`) đều tuân thủ 100% abstract methods của các Repository Ports.

```bash
# Chạy test kiểm tra contract của các Ports
backend/.venv/bin/pytest backend/tests/unit/test_homework_ports_contract.py -v
```
**Expected Outcome**: 100% tests PASS, xác nhận `issubclass(HomeworkRepository, HomeworkRepositoryPort)` và `issubclass(InMemoryHomeworkRepository, HomeworkRepositoryPort)`.

---

### Scenario 2: In-Memory Use Case Behavior Tests (Zero-Mock)
Chạy bài test kiểm tra luồng Use Case hoàn chỉnh (`CheckOverdueHomeworkUseCase`, `GetUserHomeworkSubmissionsUseCase`) sử dụng In-Memory Repositories mà không dùng bất kỳ `MagicMock` nào cho database.

```bash
# Chạy test use case với In-Memory Repositories
backend/.venv/bin/pytest backend/tests/unit/test_homework_in_memory_use_cases.py -v
```
**Expected Outcome**: Test chạy trong < 0.1 giây, 100% tests PASS, dữ liệu lưu và nạp thực sự từ RAM.

---

### Scenario 3: Ruff Linter & Architecture Boundary Check
Kiểm tra cấu trúc file và ranh giới import (Domain Ports không import SQLAlchemy).

```bash
# Kiểm tra linter toàn bộ module homework
backend/.venv/bin/ruff check backend/app/homework
```
**Expected Outcome**: 0 errors / 0 warnings.

---

### Scenario 4: Full System Regression Test
Chạy toàn bộ test suite của hệ thống để đảm bảo việc kế thừa Ports không gây ảnh hưởng đến các module khác.

```bash
# Chạy toàn bộ integration & unit test suite
backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py backend/tests/integration/test_homework_*.py -v
```
**Expected Outcome**: Toàn bộ tests PASS 100%.
