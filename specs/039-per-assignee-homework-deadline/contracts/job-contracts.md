# Phase 1: Contracts & Interfaces (039-per-assignee-homework-deadline)

## 1. Repository Contracts

### `HomeworkAssigneeRepository` (`backend/app/homework/infrastructure/homework_assignee_repository.py`)

```python
class HomeworkAssigneeRepository:
    def assign_users(
        self, homework_id: int, user_ids: set[int] | list[int], deadline: datetime
    ) -> None:
        """Tạo hoặc phục hồi phân công bài tập kèm deadline riêng cho từng user."""
        ...

    def get_by_deadline_date(
        self, target_date: date
    ) -> list[DueHomeworkAssignment]:
        """
        Truy vấn các bản ghi phân công có date(assignee.deadline AT TIME ZONE 'Asia/Ho_Chi_Minh') == target_date.
        Trả về danh sách DueHomeworkAssignment kèm thông tin bài tập để đối soát vi phạm.
        """
        ...

    def get_user_deadline(
        self, homework_id: int, user_id: int
    ) -> datetime | None:
        """Lấy deadline cá nhân của học viên đối với một bài tập cụ thể."""
        ...

    def update_deadline(
        self, homework_id: int, user_id: int, new_deadline: datetime
    ) -> bool:
        """Cập nhật deadline cá nhân của học viên."""
        ...
```

---

## 2. Strategy Contracts

### `PostponeStrategy` (`backend/app/permission_request/application/strategies/postpone_strategy.py`)

```python
class PostponeStrategy(PermissionStrategy[PostponePayload]):
    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo

    def validate(self, request: PermissionRequest[PostponePayload]) -> None:
        """
        1. Kiểm tra tồn tại bài tập.
        2. Lấy current_deadline = homework_assignee_repo.get_user_deadline(homework_id, request.user_id).
        3. Kiểm tra extended_deadline > current_deadline.
        4. Kiểm tra extended_deadline - current_deadline <= 4 ngày.
        """
        ...

    async def on_created(
        self, request: PermissionRequest[PostponePayload], user_id: int
    ) -> None:
        """
        1. Ghi nhận snapshot: request.payload.old_deadline = current_deadline.
        2. Cập nhật: homework_assignee_repo.update_deadline(homework_id, user_id, request.payload.start_time).
        """
        ...

    def on_deleted(
        self, request: PermissionRequest[PostponePayload], user_id: int
    ) -> None:
        """
        Khi đơn bị xoá: Nếu có old_deadline trong payload -> Hoàn nguyên deadline cá nhân của học viên.
        """
        ...
```

---

## 3. Use Case Contracts

### `CheckOverdueHomeworkUseCase` (`backend/app/homework/application/check_overdue_homework_use_case.py`)

```python
class CheckOverdueHomeworkUseCase:
    """
    Quét bài tập quá hạn theo deadline cá nhân của từng assignee trong Database.
    """

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        ...

    async def execute(self, target_date: date | None = None) -> int:
        """
        1. Nếu target_date is None: target_date = today_vn - 2 days.
        2. due_assignments = self.homework_assignee_repo.get_by_deadline_date(target_date).
        3. Với mỗi assignment (user_id, homework_id, deadline):
           - Đối soát submitted_at <= assignment.deadline trong DB.
           - Nếu thiếu bài tập -> Bắn HomeworkOverdueDetected(user_id, homework_id, deadline_date=...).
        4. Trả về số lượng vi phạm đã phát hiện.
        """
        ...
```
