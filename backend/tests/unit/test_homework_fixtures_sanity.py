"""
Sanity tests verifying that shared test fixtures in tests/fixtures/homework_fixtures.py
are automatically loaded via conftest and provide clean isolated state.
"""

from datetime import UTC, datetime

import pytest

from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    Homework,
)
from app.homework.domain.value_objects import AssigneeUserInfo
from tests.fixtures.homework_fixtures import (
    FakeQuizApiClient,
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    SpyEventBus,
)


@pytest.mark.asyncio
async def test_shared_fixtures_isolation(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """Xác minh các fixture được nạp tự động, độc lập và cung cấp đầy đủ chức năng."""
    # 1. Homework Repo
    hw = in_memory_homework_repo.save(Homework(id=1, title="Test HW", slug="test-hw"))
    assert in_memory_homework_repo.get_by_id(1) == hw
    assert in_memory_homework_repo.get_by_slug("test-hw") == hw

    # 2. Assignee Repo
    dl = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
    in_memory_assignee_repo.set_assignees(
        1, [AssigneeUserInfo(user_id=10, name="Alice", avatar_url=None, deadline=dl)]
    )
    assert in_memory_assignee_repo.get_user_deadline(1, 10) == dl
    assert in_memory_assignee_repo.count() == 1

    # 3. Submission Repo
    sub = CodingHomeworkSubmission.create_coding(
        homework_id=1,
        user_id=10,
        exercise_id="ex1",
        submitted_at=dl,
        is_passed=True,
    )
    in_memory_submission_repo.add(sub)
    assert in_memory_submission_repo.count() == 1

    # 4. Fake Quiz API
    fake_quiz_api.set_lesson_exercises("test-hw", [{"id": "ex1", "title": "Ex 1"}])
    exercises = await fake_quiz_api.get_lesson_exercises("test-hw")
    assert exercises is not None and len(exercises) == 1

    # 5. Spy Event Bus
    assert len(spy_event_bus.published_events) == 0
