# Quickstart & Verification Guide

## Mục tiêu kiểm thử
1. Mỗi use case trong `permission_request` nằm trên 1 file riêng biệt.
2. Không còn file gộp `use_cases.py`.
3. Toàn bộ endpoints và DI container hoạt động bình thường, 161 unit tests pass 100%.

## Lệnh kiểm tra

### 1. Kiểm tra cấu trúc thư mục
```bash
ls -la backend/app/permission_request/application/
```
Kỳ vọng: Có đủ 7 file use case riêng biệt và không còn `use_cases.py`.

### 2. Chạy Linter / Import Check
```bash
uv run --directory backend ruff check app/permission_request/
```
Kỳ vọng: All checks passed.

### 3. Chạy Toàn Bộ Test Suite
```bash
uv run --directory backend pytest tests/unit/
```
Kỳ vọng: 161/161 passed (100%).
