# Quickstart & Verification Guide: Modular Homework Repositories

## 1. Mục tiêu kiểm thử

Xác minh tính đúng đắn sau khi phân rã `repository.py` thành 3 repositories độc lập:
1. `HomeworkRepository`: CRUD bài tập và phân trang trực tiếp bằng SQL JOIN với bảng `homework_assignees`.
2. `HomeworkSubmissionRepository`: Quản lý bài nộp.
3. `HomeworkAssigneeRepository`: Quản lý phân công học viên.
4. Xóa hoàn toàn file cũ `repository.py` mà không có bất kỳ import bị hỏng.
5. Kiểm tra thời gian phản hồi và độ chính xác của các endpoint bài tập.

## 2. Các bước chạy kiểm thử tự động

### Bước 1: Kiểm tra Test Suite Homework API
```bash
backend/.venv/bin/pytest backend/tests/api/test_homework_api.py -v
```
**Kỳ vọng**: 30/30 tests passed 100%.

### Bước 2: Kiểm tra Test Suite Report API (Báo cáo bài tập chưa nộp)
```bash
backend/.venv/bin/pytest backend/tests/api/test_report_api.py -v
```
**Kỳ vọng**: 12/12 tests passed 100%.

### Bước 3: Kiểm tra static analysis và import cũ
```bash
grep -rn "from app.homework.infrastructure.repository import" backend/
```
**Kỳ vọng**: Không còn bất kỳ file nào import từ `app.homework.infrastructure.repository`.

## 3. Kiểm tra kịch bản nghiệp vụ trực tiếp (End-to-End Scenarios)

### Kịch bản 1: Lấy danh sách bài tập của cá nhân (`/api/v1/homeworks/me`)
1. User đăng nhập có `user_id = X`.
2. Gọi `GET /api/v1/homeworks/me?page=1&page_size=20`.
3. Kiểm tra câu lệnh SQL sinh ra: Có mệnh đề `JOIN homework_assignees ON homeworks.id = homework_assignees.homework_id WHERE homework_assignees.user_id = X AND homework_assignees.is_deleted = false`.
4. Không thực hiện in-memory filtering trên danh sách 1000 bản ghi.

### Kịch bản 2: Đồng bộ bài tập Quiz / Coding
1. Gọi `POST /api/v1/homeworks/{id}/sync`.
2. `SyncHomeworkUseCase` inject `HomeworkRepository` và `HomeworkSubmissionRepository`.
3. Bài nộp được tạo hoặc cập nhật chính xác trong cơ sở dữ liệu.
