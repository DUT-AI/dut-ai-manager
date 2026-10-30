# Quickstart & Verification Guide

## Mục tiêu kiểm thử
1. Hệ thống xử lý đơn xin phép chuyển dịch 100% sang Strategy Pattern.
2. Mỗi loại đơn (`ABSENCE`, `LATE`, `POSTPONE`, `OTHER`) được quản lý bởi 1 Handler riêng biệt.
3. Thêm một loại đơn mới không cần sửa đổi `CreatePermissionRequestUseCase` hay `DeletePermissionRequestUseCase`.
4. Toàn bộ 168 unit tests hiện có pass 100%.

## Lệnh kiểm tra

### 1. Chạy Linter
```bash
uv run --directory backend ruff check app/permission_request/
```
Kỳ vọng: All checks passed.

### 2. Chạy Kiểm Thử Unit Test
```bash
uv run --directory backend pytest tests/unit/
```
Kỳ vọng: 168/168 tests pass (100%).
