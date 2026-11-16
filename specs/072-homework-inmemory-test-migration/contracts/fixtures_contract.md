# Contract: Test Fixtures & In-Memory Harness

**Feature**: `072-homework-inmemory-test-migration`  
**Date**: 2026-11-16  

---

## 1. Test Fixtures Contract

Các fixtures được cung cấp tập trung tại `backend/tests/fixtures/homework_fixtures.py` (hoặc conftest) tuân thủ hợp đồng:

```python
import pytest
from app.homework.infrastructure.in_memory import (
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    InMemoryHomeworkAssigneeRepository,
)

@pytest.fixture
def in_memory_homework_repo() -> InMemoryHomeworkRepository:
    """Trả về một instance InMemoryHomeworkRepository mới, hoàn toàn sạch (trống)."""
    ...

@pytest.fixture
def in_memory_submission_repo() -> InMemoryHomeworkSubmissionRepository:
    """Trả về một instance InMemoryHomeworkSubmissionRepository mới, hoàn toàn sạch (trống)."""
    ...

@pytest.fixture
def in_memory_assignee_repo() -> InMemoryHomeworkAssigneeRepository:
    """Trả về một instance InMemoryHomeworkAssigneeRepository mới, hoàn toàn sạch (trống)."""
    ...

@pytest.fixture
def fake_quiz_api() -> FakeQuizApiClient:
    """Trả về một FakeQuizApiClient hỗ trợ nạp sẵn metadata bài tập con trong RAM."""
    ...

@pytest.fixture
def spy_event_bus() -> SpyEventBus:
    """Trả về một SpyEventBus ghi nhận toàn bộ domain events phát ra trong test."""
    ...
```

---

## 2. In-Memory Assertion Contract

Các bài test di chuyển từ Mock sang In-Memory PHẢI tuân thủ hợp đồng kiểm tra trạng thái:

1. **Thay thế `assert_called_once_with`**:
   - *Cũ*: `mock_assignee_repo.assign_users.assert_called_once_with(...)`
   - *Mới*: Kiểm tra trạng thái thực tế sau khi thực thi:
     ```python
     assert in_memory_assignee_repo.get_user_deadline(hw_id, user_id) == expected_deadline
     ```

2. **Thay thế `mock.get_by_id.return_value`**:
   - *Cũ*: `mock_repo.get_by_id.return_value = Homework(...)`
   - *Mới*: Nạp trực tiếp vào RAM:
     ```python
     in_memory_homework_repo.save(Homework(id=1, title="BT", ...))
     ```

3. **Thay thế Mock EventBus**:
   - *Cũ*: `mock_event_bus.publish.assert_awaited()`
   - *Mới*:
     ```python
     assert len(spy_event_bus.published_events) == 1
     event = spy_event_bus.published_events[0]
     assert isinstance(event, HomeworkOverdueDetected)
     assert event.user_id == 101
     ```
