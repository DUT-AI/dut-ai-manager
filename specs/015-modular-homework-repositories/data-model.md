# Phase 1: Data Model & Repository Interfaces

## 1. Domain Entities & Database Mapping

Không thay đổi cấu trúc bảng cơ sở dữ liệu (`homeworks`, `homework_submissions`, `homework_assignees`). Các thực thể domain giữ nguyên:
- `Homework`: Aggregate root đại diện cho bài tập.
- `HomeworkSubmission`: Thực thể ghi nhận bài nộp (coding hoặc game).
- `HomeworkAssignee`: Thực thể liên kết phân công học viên.

## 2. Repository Specifications

### 2.1. `HomeworkRepository` (`infrastructure/homework_repository.py`)

Chuyên trách bảng `homeworks` (`HomeworkModel`).

```python
class HomeworkRepository:
    def __init__(self, session: Session): ...

    def get_all(
        self,
        query_support: QuerySupport | None = None,
        skip: int = 0,
        limit: int = 100,
        deleted: bool = False,
    ) -> list[HomeworkEntity]: ...

    def get_paged(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HomeworkEntity], int]: ...

    def get_assigned_to_user_paged(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        deleted: bool = False,
    ) -> tuple[list[HomeworkEntity], int]:
        """Lấy danh sách bài tập được giao cho user với phân trang trực tiếp từ SQL JOIN."""
        ...

    def get_all_assigned_to_user(
        self,
        user_id: int,
        deleted: bool = False,
    ) -> list[HomeworkEntity]:
        """Lấy tất cả bài tập được giao cho user thông qua SQL JOIN."""
        ...

    def get_by_id(self, homework_id: int, deleted: bool = False) -> HomeworkEntity | None: ...
    def create(self, homework: HomeworkEntity) -> HomeworkEntity: ...
    def update(self, homework: HomeworkEntity) -> HomeworkEntity | None: ...
    def delete_by_id(self, homework_id: int) -> bool: ...
    def soft_delete(self, homework_id: int) -> bool: ...
    def restore(self, homework_id: int) -> HomeworkEntity | None: ...
    def get_by_slug(self, slug: str) -> HomeworkEntity | None: ...
    def get_by_deadline_date(self, target_date: Any) -> list[HomeworkEntity]: ...
```

### 2.2. `HomeworkSubmissionRepository` (`infrastructure/homework_submission_repository.py`)

Chuyên trách bảng `homework_submissions` (`HomeworkSubmissionModel`).

```python
class HomeworkSubmissionRepository:
    def __init__(self, session: Session): ...

    def add_submission(self, submission: HomeworkSubmissionEntity) -> HomeworkSubmissionEntity: ...
    def get_submissions_by_user(self, homework_id: int, user_id: int) -> list[HomeworkSubmissionEntity]: ...
    def get_user_submissions_for_homeworks(self, homework_ids: list[int], user_id: int) -> list[HomeworkSubmissionEntity]: ...
    def get_all_submissions(self) -> list[HomeworkSubmissionEntity]: ...
    def has_valid_submission(self, homework_id: int, user_id: int, submission_type: Any, deadline: datetime) -> bool: ...
    def get_submissions_by_homework(self, homework_id: int) -> list[HomeworkSubmissionEntity]: ...
    def find_submission_match(
        self,
        homework_id: int,
        user_id: int,
        submission_type: Any,
        exercise_id: str | None = None,
        quiz_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmissionModel | None: ...
    def update_submission(self, model: HomeworkSubmissionModel, ...) -> HomeworkSubmissionEntity: ...
    def get_submissions_by_exercise(self, homework_id: int, exercise_id: str) -> list[HomeworkSubmissionEntity]: ...
    def get_submitted_exercise_ids(self, homework_id: int, user_id: int, deadline: datetime | None = None) -> set[str]: ...
```

### 2.3. `HomeworkAssigneeRepository` (`infrastructure/homework_assignee_repository.py`)

Chuyên trách bảng `homework_assignees` (`HomeworkAssigneeModel`).

```python
class HomeworkAssigneeRepository:
    def __init__(self, session: Session): ...

    def sync_assignees(self, homework_id: int, assignee_ids: list[int] | None) -> None: ...
    def get_assigned_user_ids(self, homework_id: int) -> set[int]: ...
    def get_assigned_homework_ids(self, user_id: int) -> list[int]: ...
    def add_assignees(self, homework_id: int, user_ids: list[int]) -> None: ...
    def remove_assignees(self, homework_id: int, user_ids: list[int]) -> None: ...
```

## 3. Dependency Injection Mapping (Dishka)

| Component / Use Case | Required Repositories |
|----------------------|-----------------------|
| `GetHomeworksPagedUseCase` | `HomeworkRepository` |
| `GetHomeworkDetailUseCase` | `HomeworkRepository` |
| `GetUserHomeworksUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository` |
| `GetUnsubmittedHomeworksForUserUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository` |
| `GetUnsubmittedHomeworkReportUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository`, `UserRepository` |
| `CreateHomeworkUseCase` | `HomeworkRepository`, `HomeworkAssigneeRepository` |
| `UpdateHomeworkUseCase` | `HomeworkRepository`, `HomeworkAssigneeRepository` |
| `DeleteHomeworkUseCase` | `HomeworkRepository` |
| `RecordSubmissionUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository` |
| `SyncHomeworkUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository` |
| `GetUserHomeworkSubmissionsUseCase` | `HomeworkSubmissionRepository` |
| `GetHomeworkSubmissionStatusUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository`, `HomeworkAssigneeRepository` |
| `CheckOverdueHomeworkUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository` |
| `RescanAllHomeworksUseCase` | `HomeworkRepository`, `HomeworkSubmissionRepository` |
