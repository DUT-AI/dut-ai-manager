from datetime import UTC, datetime

from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    Homework,
    SubmissionType,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import (
    HomeworkRepository,
)
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.in_memory import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
)


def test_adapters_satisfy_port_contracts():
    """Xác minh cả hai adapter (SQLAlchemy và InMemory) tuân thủ 100% các Port interfaces."""
    assert issubclass(HomeworkRepository, HomeworkRepositoryPort)
    assert issubclass(InMemoryHomeworkRepository, HomeworkRepositoryPort)

    assert issubclass(HomeworkSubmissionRepository, HomeworkSubmissionRepositoryPort)
    assert issubclass(InMemoryHomeworkSubmissionRepository, HomeworkSubmissionRepositoryPort)

    assert issubclass(HomeworkAssigneeRepository, HomeworkAssigneeRepositoryPort)
    assert issubclass(InMemoryHomeworkAssigneeRepository, HomeworkAssigneeRepositoryPort)


def test_in_memory_homework_repo_crud_fidelity():
    """Xác minh tính đúng đắn hoạt động CRUD của InMemoryHomeworkRepository."""
    repo = InMemoryHomeworkRepository()
    hw = Homework(title="Test Course", slug="test-course", requires_coding=True)

    created = repo.create(hw)
    assert created.id == 1
    assert repo.get_by_id(1) == created
    assert repo.get_by_slug("test-course") == created

    # Test update
    updated_hw = created.model_copy(update={"title": "Updated Course"})
    repo.save(updated_hw)
    assert repo.get_by_id(1).title == "Updated Course"

    # Test delete
    assert repo.delete_by_id(1) is True
    assert repo.get_by_id(1) is None


def test_in_memory_submission_repo_fidelity():
    """Xác minh tính đúng đắn của InMemoryHomeworkSubmissionRepository."""
    repo = InMemoryHomeworkSubmissionRepository()
    sub = CodingHomeworkSubmission.create_coding(
        homework_id=10,
        user_id=42,
        exercise_id="ex-1",
        submitted_at=datetime.now(UTC),
        is_passed=True,
    )

    saved = repo.add_submission(sub)
    assert saved.id == 1
    assert len(repo.get_submissions_by_user(10, 42)) == 1
    assert repo.get_submitted_exercise_ids(10, 42) == {"ex-1"}

    matched = repo.find_submission_match(
        homework_id=10,
        user_id=42,
        submission_type=SubmissionType.CODING,
        exercise_id="ex-1",
    )
    assert matched is not None
    assert matched.id == 1


def test_in_memory_assignee_repo_fidelity():
    """Xác minh tính đúng đắn của InMemoryHomeworkAssigneeRepository."""
    repo = InMemoryHomeworkAssigneeRepository()
    deadline = datetime(2026, 12, 1, 23, 59, 59, tzinfo=UTC)

    repo.assign_users(homework_id=5, user_ids=[101, 102], deadline=deadline)
    assert repo.get_assigned_user_ids(5) == {101, 102}
    assert repo.get_user_deadline(5, 101) == deadline

    # Test update deadline (hoãn bài)
    new_dl = datetime(2026, 12, 5, 23, 59, 59, tzinfo=UTC)
    repo.update_deadline(5, 101, new_dl)
    assert repo.get_user_deadline(5, 101) == new_dl
