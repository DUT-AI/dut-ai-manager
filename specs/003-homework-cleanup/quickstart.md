# Quickstart & Verification Guide: Domain Homework Cleanup

**Feature**: `003-homework-cleanup` | **Date**: 2026-09-25

---

## 1. Prerequisites

- Python 3.12+ và `uv` package manager.
- PostgreSQL database đang chạy.

---

## 2. Các Bước Kiểm Tra và Xác Minh

### Bước 1: Áp dụng Migration Alembic Drop bảng `homework_teams`
```bash
cd backend
uv run alembic upgrade head
```
*Kỳ vọng:* Migration thực thi thành công, bảng `homework_teams` được xóa khỏi DB.

---

### Bước 2: Kiểm tra Static Typing với `ty`
```bash
cd backend
uv run ty check app --exclude alembic/ --exclude tests/ --exclude scripts/ --exclude app/scripts/ --force-exclude
```
*Kỳ vọng:* 0 lỗi Typecheck. Không còn bất kỳ tham chiếu lỗi nào về `HomeworkTeamModel` hay `HomeworkSubmission`.

---

### Bước 3: Chạy Toàn Bộ Unit Test của Module Homework
```bash
cd backend
uv run pytest tests/ -k homework -v
```
*Kỳ vọng:* 100% tests liên quan đến Homework pass.

---

### Bước 4: Kiểm tra Tạo Bài Tập & Phân Công Cá Nhân
1. Gửi request tạo bài tập với `assignee_ids=[1, 2]`.
2. Kiểm tra trong DB: Bảng `homework_assignees` có 2 bản ghi tương ứng với `homework_id`.
3. Kiểm tra API `GET /homeworks/{id}` trả về `assignee_ids=[1, 2]`.
