# Quickstart & Verification: DB-First Submissions & Manual Sync

**Feature**: `013-fix-my-homeworks-coding-submitted` | **Date**: 2026-10-17

## 1. Kiểm Thử Backend

Chạy test API bài tập:
```bash
backend/.venv/bin/pytest backend/tests/api/test_homework_api.py -v
```

## 2. Kiểm Thử Frontend Build

Kiểm tra build không có lỗi TypeScript:
```bash
cd frontend && npm run build
```

## 3. Xác Minh Trực Quan Trên Web Browser

1. Đăng nhập tài khoản học viên tại `http://localhost:5173/dashboard/my-homeworks`.
2. Kiểm tra tốc độ nạp trang: Dữ liệu tải lên tức thì mà không phải chờ các API ngoài Quiz phản hồi.
3. Refresh trang liên tục 10 lần: Trạng thái các thẻ bài tập giữ nguyên 100% tính nhất quán.
4. Với bài tập chưa nộp hoặc vừa nộp trên Quiz: Bấm nút **"Đồng bộ kết quả"** và quan sát trạng thái tự động chuyển sang xanh lá.
