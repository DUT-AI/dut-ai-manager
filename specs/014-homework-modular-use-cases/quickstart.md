# Quickstart: Kiểm Thử & Xác Minh Đợt Tách Use Case Homework (014-homework-modular-use-cases)

## 1. Mục Tiêu Kiểm Thử
- Đảm bảo tất cả 5 Use Case mới hoạt động độc lập và chính xác 100%.
- Không phát sinh lỗi import từ Dishka provider hay Controller.
- Không gây hồi quy (Zero-regression) trên toàn bộ hệ thống API bài tập và báo cáo.

## 2. Kịch Bản Kiểm Thử Tự Động (Automated Testing)

### Bước 1: Chạy toàn bộ test suite của homework
```bash
backend/.venv/bin/pytest backend/tests/api/test_homework_api.py -v
```
*Kỳ vọng*: 30/30 tests pass.

### Bước 2: Chạy kiểm thử cho module report (vì report phụ thuộc vào unsubmitted homework use case)
```bash
backend/.venv/bin/pytest backend/tests/api/ -k "report or homework" -v
```

### Bước 3: Kiểm tra frontend compilation
```bash
npm --prefix frontend run build
```
*Kỳ vọng*: Build Vite thành công trong ~6 giây mà không phát sinh lỗi TypeScript.
