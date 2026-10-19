# Quickstart: Xác Minh Loại Bỏ `assignee_ids` Khỏi Entity `Homework`

## 1. Mục Tiêu Kiểm Thử
Chứng minh rằng:
1. `Homework` domain entity không còn trường `assignee_ids`.
2. Tạo mới / cập nhật bài tập có truyền `assignee_ids` vẫn lưu và phân công đúng học viên qua `HomeworkAssigneeRepository`.
3. Toàn bộ API và Use Case kiểm tra quá hạn, báo cáo chưa nộp hoạt động ổn định.

## 2. Các Bước Kiểm Thử

### Bước 1: Chạy toàn bộ Unit & Integration Test
```bash
cd backend
uv run pytest tests/api/test_homework_api.py -v
uv run pytest tests/unit/test_homework_*.py -v
uv run pytest tests/integration/test_homework_quiz_integration.py -v
```
**Kỳ vọng**: 100% test cases PASSED.

### Bước 2: Kiểm thử thủ công tạo bài tập với assignees
```bash
# Tạo bài tập kèm assignee_ids = [1]
# Kiểm tra trong homework_assignees table có bản ghi liên kết
```
