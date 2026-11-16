# Contract: Homework Repository Ports Specification

**Package**: `backend/app/homework/domain/ports/`  
**Standard**: Pure Python `abc.ABC` Abstract Base Classes  

---

## 1. `HomeworkRepositoryPort`

```python
from abc import ABC, abstractmethod
from app.homework.domain.entity import Homework as HomeworkEntity

class HomeworkRepositoryPort(ABC):
    """Cổng giao tiếp trừu tượng lưu trữ và truy xuất thông tin bài tập (Homework)."""

    @abstractmethod
    def get_all(self, deleted: bool = False) -> list[HomeworkEntity]: ...

    @abstractmethod
    def get_paged(
        self, page: int, page_size: int, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], int, dict[int, datetime | None]]: ...

    @abstractmethod
    def get_by_id(self, homework_id: int) -> HomeworkEntity | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> HomeworkEntity | None: ...

    @abstractmethod
    def create(self, homework: HomeworkEntity) -> HomeworkEntity: ...

    @abstractmethod
    def update(self, homework: HomeworkEntity) -> HomeworkEntity | None: ...

    @abstractmethod
    def save(self, homework: HomeworkEntity) -> HomeworkEntity: ...

    @abstractmethod
    def delete(self, homework_id: int) -> bool: ...

    @abstractmethod
    def delete_by_id(self, homework_id: int) -> bool: ...
```

---

## 2. `HomeworkSubmissionRepositoryPort`

```python
from abc import ABC, abstractmethod
from datetime import datetime
from app.homework.domain.entity import HomeworkSubmission, SubmissionType
from app.homework.domain.value_objects import CodingSubmissionDetails, GameSubmissionDetails

class HomeworkSubmissionRepositoryPort(ABC):
    """Cổng giao tiếp trừu tượng lưu trữ lịch sử nộp bài tập (Audit trail)."""

    @abstractmethod
    def add_submission(self, submission: HomeworkSubmission) -> HomeworkSubmission: ...

    @abstractmethod
    def update_submission(
        self,
        submission: HomeworkSubmission,
        submitted_at: datetime,
        is_passed: bool,
        exercise_id: str | None = None,
        exercise_title: str | None = None,
        score: float | None = None,
        attempt_number: int = 1,
        details: CodingSubmissionDetails | GameSubmissionDetails | None = None,
    ) -> HomeworkSubmission: ...

    @abstractmethod
    def get_submissions_by_user(
        self, homework_id: int, user_id: int
    ) -> list[HomeworkSubmission]: ...

    @abstractmethod
    def get_submissions_by_homework(
        self, homework_id: int
    ) -> list[HomeworkSubmission]: ...

    @abstractmethod
    def find_submission_match(
        self,
        homework_id: int,
        user_id: int,
        submission_type: SubmissionType,
        exercise_id: str | None = None,
        quiz_submission_id: str | None = None,
        submitted_at: datetime | None = None,
    ) -> HomeworkSubmission | None: ...

    @abstractmethod
    def get_submitted_exercise_ids(
        self, homework_id: int, user_id: int
    ) -> set[str]: ...
```

---

## 3. `HomeworkAssigneeRepositoryPort`

```python
from abc import ABC, abstractmethod
from datetime import date, datetime
from app.homework.infrastructure.homework_assignee_repository import (
    AssigneeUserInfo,
    DueHomeworkAssignment,
)

class HomeworkAssigneeRepositoryPort(ABC):
    """Cổng giao tiếp trừu tượng quản lý phân công học viên và hạn nộp cá nhân."""

    @abstractmethod
    def sync_assignees(
        self,
        homework_id: int,
        assignee_ids: list[int] | None,
        default_deadline: datetime | None = None,
        force_override: bool = False,
    ) -> None: ...

    @abstractmethod
    def assign_users(
        self,
        homework_id: int,
        user_ids: set[int] | list[int],
        deadline: datetime,
        force_override: bool = False,
    ) -> None: ...

    @abstractmethod
    def get_user_deadline(
        self, homework_id: int, user_id: int
    ) -> datetime | None: ...

    @abstractmethod
    def get_assigned_user_ids(self, homework_id: int) -> set[int]: ...

    @abstractmethod
    def get_by_deadline_date(
        self, target_date: date
    ) -> list[DueHomeworkAssignment]: ...

    @abstractmethod
    def get_assignees_with_user_info(
        self, homework_id: int
    ) -> list[AssigneeUserInfo]: ...

    @abstractmethod
    def get_assigned_homework_ids(self, user_id: int) -> list[int]: ...
```
