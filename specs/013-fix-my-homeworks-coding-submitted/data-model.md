# Data Model & Query Flow: DB-First Homework Submissions

**Feature**: `013-fix-my-homeworks-coding-submitted` | **Date**: 2026-10-17

## 1. Truy Vấn Dữ Liệu Bài Nộp Của Người Dùng

Trong `HomeworkRepository`, bổ sung phương thức tra cứu danh sách submission của 1 user cho danh sách các bài tập:

```python
def get_user_submissions_for_homeworks(
    self, homework_ids: list[int], user_id: int
) -> list[HomeworkSubmissionEntity]:
    statement = (
        select(HomeworkSubmissionModel)
        .where(
            HomeworkSubmissionModel.homework_id.in_(homework_ids),
            HomeworkSubmissionModel.user_id == user_id,
        )
    )
    return [m.to_entity() for m in self.session.scalars(statement).all()]
```

## 2. Tiêu Chuẩn Xác Định Trạng Thái

Từ danh sách submissions lấy được:
- `coding_submitted = any(s.submission_type == HomeworkSubmissionType.CODING for s in user_subs)`
- `game_submitted = any(s.submission_type == HomeworkSubmissionType.GAME and s.is_passed for s in user_subs)`
- `is_submitted` được tính toán theo quy tắc:
  - Nếu `requires_coding` và `requires_game`: Cần cả 2 đều True.
  - Nếu chỉ `requires_coding`: Cần `coding_submitted == True`.
  - Nếu chỉ `requires_game`: Cần `game_submitted == True`.
  - Fallback: Nếu không khai báo rõ ràng, bất kỳ phần nào có nộp đều tính là True nếu có bài nộp tương ứng.
