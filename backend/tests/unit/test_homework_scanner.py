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
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
)


def test_scanner_includes_partially_submitted_homework(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
):
    """Kiểm tra học sinh mới làm 1/2 bài coding thì scanner KHÔNG bỏ qua mà tạo reminder."""
    now = datetime(2026, 11, 15, 10, 0, 0, tzinfo=UTC)
    deadline = now + timedelta(hours=4)  # Khớp mốc OFFSET_4H (3.5h - 4.5h)

    hw = Homework(
        id=1,
        title="Bài tập có 2 bài con",
        requires_coding=True,
        requires_game=False,
    )
    in_memory_homework_repo.save(hw)

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

    # Đề bài có 2 bài tập con: ex-1 và ex-2 (được ghi nhận qua submissions của bài tập)
    # Học sinh khác đã nộp ex-2 để hệ thống biết bài 1 có 2 bài con
    in_memory_submission_repo.add(
        HomeworkSubmission(
            id=1,
            homework_id=1,
            user_id=99,
            submission_type=SubmissionType.CODING,
            exercise_id="ex-2",
            is_passed=True,
            submitted_at=now - timedelta(days=1),
        )
    )

    # Học sinh 10 chỉ nộp 1 bài ex-1
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
    )

    candidates = scanner.scan_pending_tasks(now)

    assert len(candidates) == 1
    assert candidates[0].task_id == 1
    assert candidates[0].user_id == 10
