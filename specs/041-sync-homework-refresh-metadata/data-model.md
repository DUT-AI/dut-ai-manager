# Data Model & Contracts: Làm Mới Metadata Bài Tập Khi Đồng Bộ Từ Quiz

**Feature**: `041-sync-homework-refresh-metadata`  
**Date**: 2026-11-01  

---

## 1. Domain Entities & Fields

### Homework Entity (`Homework`)
Đại diện cho bài tập trong domain, được cập nhật tự động khi có metadata mới từ Quiz API:

| Trường | Kiểu dữ liệu | Mô tả | Nguồn cập nhật |
| :--- | :--- | :--- | :--- |
| `id` | `int` | Khóa chính của bài tập | Database |
| `title` | `str` | Tiêu đề bài tập | Giữ nguyên hoặc đồng bộ tên từ Quiz |
| `slug` | `str` | Định danh duy nhất của bài học trên Quiz | Bắt buộc để đồng bộ |
| `requires_coding` | `bool` | Cờ bài tập có phần lập trình Coding | Tự động cập nhật theo `has_coding` từ Quiz |
| `requires_game` | `bool` | Cờ bài tập có phần trắc nghiệm Game | Tự động cập nhật theo `has_game` từ Quiz |

---

## 2. DTO & Response Contract

### SyncHomeworkResult (Dictionary / DTO)
Phản hồi trả về sau khi thực hiện `SyncHomeworkFromQuizUseCase.execute(homework_id)`:

```python
class SyncHomeworkResult(TypedDict):
    homework_id: int
    title: str
    requires_coding: bool
    requires_game: bool
    coding_exercises_count: int      # Tổng số bài tập coding con hiện có trên Quiz
    game_questions_count: int        # Tổng số câu hỏi game hiện có trên Quiz
    synced_coding_count: int         # Số bài nộp coding mới được thêm vào DB
    updated_coding_count: int        # Số bài nộp coding được cập nhật lại
    synced_game_count: int           # Số session game mới được thêm vào DB
    updated_game_count: int          # Số session game được cập nhật lại
    message: str                     # Thông báo chi tiết cho người dùng
```

---

## 3. Trạng Thái Vòng Đời Của Tiến Trình Đồng Bộ (Lifecycle State Transition)

```
[Bắt đầu: Admin nhấn nút "Đồng bộ từ Quiz"]
           │
           ▼
[Gọi quiz_api.get_lesson_metadata(slug) & get_lesson_exercises(slug)]
           │
     ┌─────┴────────────────────────┐
     ▼                              ▼
(Thành công)                 (Lỗi mạng / Không tìm thấy)
     │                              │
     ▼                              ▼
[Cập nhật requires_coding,    [Ghi log warning,
 requires_game, exercises      giữ cấu hình hiện tại]
 vào DB qua repo.save()]            │
     │                              │
     └──────────────┬───────────────┘
                    ▼
[Tiến hành kéo bài nộp Coding & Game từ Quiz API]
                    │
                    ▼
[Lưu/cập nhật vào bảng homework_submissions]
                    │
                    ▼
[Trả về kết quả chi tiết kèm metadata bài tập con mới]
```
