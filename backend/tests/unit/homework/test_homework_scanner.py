"""
Unit tests for HomeworkTaskScanner ensuring partial homeworks are not skipped.
Operates on In-Memory Fake Repositories (Zero-Mock).
"""

from datetime import UTC, datetime, timedelta

from app.homework.domain.entity import Homework, HomeworkSubmission, SubmissionType
from app.homework.domain.value_objects import AssigneeUserInfo
from app.reminder.application.scanners.homework_scanner import HomeworkTaskScanner
from tests.fixtures.homework_fixtures import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    make_exercise,
)


def test_scanner_includes_partially_submitted_homework(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
):
    """Kiểm tra học sinh mới làm 1/2 bài coding thì scanner KHÔNG bỏ qua mà tạo reminder."""
    now = datetime(2026, 11, 15, 10, 0, 0, tzinfo=UTC)
    deadline = now + timedelta(hours=4)

    hw = Homework(
        id=1,
        title="Bài tập có 2 bài con",
        requires_coding=True,
        requires_game=False,
    )
    in_memory_homework_repo.save(hw)
    in_memory_exercise_repo.sync_exercises(
        1, [make_exercise(1, "ex-1", "Ex 1", 1), make_exercise(1, "ex-2", "Ex 2", 2)]
    )

    in_memory_assignee_repo.set_assignees(
        1,
        [
            AssigneeUserInfo(
                user_id=10,
                deadline=deadline,
                name="Test User",
                avatar_url=None,
            )
        ],
        default_deadline=deadline,
    )

    in_memory_submission_repo.add(
        HomeworkSubmission(
            id=2,
            homework_id=1,
            user_id=10,
            submission_type=SubmissionType.CODING,
            exercise_id="ex-1",
            is_passed=True,
            submitted_at=now - timedelta(hours=1),
        )
    )

    scanner = HomeworkTaskScanner(
        homework_repo=in_memory_homework_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )

    candidates = scanner.scan_pending_tasks(now)

    assert len(candidates) == 1
    assert candidates[0].task_id == 1
    assert candidates[0].user_id == 10
