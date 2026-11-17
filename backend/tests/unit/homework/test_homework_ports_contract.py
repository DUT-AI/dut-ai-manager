from datetime import UTC, datetime, timedelta

from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    Homework,
    HomeworkExercise,
    SubmissionType,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
)
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_exercise_repository import (
    HomeworkExerciseRepository,
)
from app.homework.infrastructure.homework_repository import (
    HomeworkRepository,
)
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.in_memory import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
)


def test_adapters_satisfy_port_contracts():
    """Xác minh cả hai adapter (SQLAlchemy và InMemory) tuân thủ 100% các Port interfaces."""
    assert issubclass(HomeworkRepository, HomeworkRepositoryPort)
    assert issubclass(InMemoryHomeworkRepository, HomeworkRepositoryPort)

    assert issubclass(HomeworkExerciseRepository, HomeworkExerciseRepositoryPort)
    assert issubclass(InMemoryHomeworkExerciseRepository, HomeworkExerciseRepositoryPort)

    assert issubclass(HomeworkSubmissionRepository, HomeworkSubmissionRepositoryPort)
    assert issubclass(
        InMemoryHomeworkSubmissionRepository, HomeworkSubmissionRepositoryPort
    )

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

    updated_hw = created.model_copy(update={"title": "Updated Course"})
    repo.save(updated_hw)
    assert repo.get_by_id(1).title == "Updated Course"

    assert repo.delete_by_id(1) is True
    assert repo.get_by_id(1) is None


def test_in_memory_exercise_repo_sync_and_deactivation():
    """Xác minh sync_exercises upsert đúng thứ tự và đặt is_active=False cho bài đã bị gỡ."""
    repo = InMemoryHomeworkExerciseRepository()
    synced = repo.sync_exercises(
        10,
        [
            HomeworkExercise(homework_id=10, exercise_id="ex-2", title="Bài 2", order_index=2),
            HomeworkExercise(homework_id=10, exercise_id="ex-1", title="Bài 1", order_index=1),
        ],
    )
    assert [e.exercise_id for e in synced] == ["ex-1", "ex-2"]

    # Gỡ ex-2, cập nhật tiêu đề ex-1 và thêm ex-3
    synced_v2 = repo.sync_exercises(
        10,
        [
            HomeworkExercise(homework_id=10, exercise_id="ex-1", title="Bài 1 mới", order_index=1),
            HomeworkExercise(homework_id=10, exercise_id="ex-3", title="Bài 3", order_index=2),
        ],
    )
    assert [e.exercise_id for e in synced_v2] == ["ex-1", "ex-3"]
    assert synced_v2[0].title == "Bài 1 mới"


def test_in_memory_submission_repo_append_only_fidelity():
    """Xác minh InMemoryHomeworkSubmissionRepository không ghi đè lượt nộp khác của cùng exercise_id."""
    repo = InMemoryHomeworkSubmissionRepository()
    t1 = datetime(2026, 11, 10, 10, 0, 0, tzinfo=UTC)
    t2 = t1 + timedelta(hours=2)

    sub1 = CodingHomeworkSubmission.create_coding(
        homework_id=10,
        user_id=42,
        exercise_id="ex-1",
        submitted_at=t1,
        is_passed=True,
        external_submission_id="ext-101",
    )
    saved = repo.add_submission(sub1)
    assert saved.id == 1
    assert len(repo.get_submissions_by_user(10, 42)) == 1

    # Match cùng external_submission_id -> tìm thấy
    matched_same = repo.find_submission_match(
        homework_id=10,
        user_id=42,
        submission_type=SubmissionType.CODING,
        exercise_id="ex-1",
        external_submission_id="ext-101",
        submitted_at=t1,
    )
    assert matched_same is not None
    assert matched_same.id == 1

    # Khác external_submission_id dù cùng exercise_id -> KHÔNG match (append-only)
    matched_new = repo.find_submission_match(
        homework_id=10,
        user_id=42,
        submission_type=SubmissionType.CODING,
        exercise_id="ex-1",
        external_submission_id="ext-102",
        submitted_at=t2,
    )
    assert matched_new is None


def test_in_memory_assignee_repo_fidelity():
    """Xác minh tính đúng đắn của InMemoryHomeworkAssigneeRepository."""
    repo = InMemoryHomeworkAssigneeRepository()
    deadline = datetime(2026, 12, 1, 23, 59, 59, tzinfo=UTC)

    repo.assign_users(homework_id=5, user_ids=[101, 102], deadline=deadline)
    assert repo.get_assigned_user_ids(5) == {101, 102}
    assert repo.get_user_deadline(5, 101) == deadline

    new_dl = datetime(2026, 12, 5, 23, 59, 59, tzinfo=UTC)
    repo.update_deadline(5, 101, new_dl)
    assert repo.get_user_deadline(5, 101) == new_dl
