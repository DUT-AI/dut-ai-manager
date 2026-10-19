# Data Model & Query Mapping: Tối Ưu Hóa Tải Danh Sách Bài Nộp

## 1. SQL JOIN Query Design

Thay vì nạp toàn bộ User qua Python, bổ sung phương thức truy vấn tối ưu tại `HomeworkRepository`:

```python
class AssigneeUserInfo(NamedTuple):
    user_id: int
    name: str
    avatar_url: str | None

def get_assignees_with_user_info(self, homework_id: int) -> list[AssigneeUserInfo]:
    """
    Truy vấn duy nhất 1 câu SQL JOIN lấy toàn bộ học viên được giao bài tập
    kèm thông tin họ tên và avatar.
    """
    statement = (
        select(
            HomeworkAssigneeModel.user_id,
            UserModel.name,
            UserModel.avatar_url,
        )
        .join(UserModel, HomeworkAssigneeModel.user_id == UserModel.id)
        .where(
            HomeworkAssigneeModel.homework_id == homework_id,
            HomeworkAssigneeModel.is_deleted == False,
            UserModel.is_deleted == False,
        )
        .order_by(UserModel.name.asc())
    )
    rows = self.session.execute(statement).all()
    return [
        AssigneeUserInfo(user_id=r[0], name=r[1], avatar_url=r[2])
        for r in rows
    ]
```

## 2. In-Memory Aggregation trong Use Case

Khi đã có:
1. `assignees = self.homework_repo.get_assignees_with_user_info(homework.id)`
2. `db_submissions = self.homework_submission_repo.get_submissions_by_homework(homework.id)`
3. `postpone_requests = self.permission_repo.get_postpone_requests_for_homeworks(...)`

Toàn bộ quá trình tính toán diễn ra thuần túy trên RAM (In-Memory Processing) với độ phức tạp $O(N)$ trong đó $N \le 100$ (số học viên và bài nộp):
- Xác định bài tập con từ các bản ghi `db_submissions` (`exercise_id`, `exercise_title`).
- Nhóm bài nộp theo từng bài tập con và tính `is_late`, `is_passed`, `score`.
- Phân loại học viên vào `coding.submitted`, `coding.not_submitted`, `game.submitted`, `game.not_submitted`, `students`.
- Tính `completion_rate` cho từng bài tập con.
