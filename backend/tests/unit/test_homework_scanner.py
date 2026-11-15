"""Unit tests for HomeworkTaskScanner ensuring partial homeworks are not skipped."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.homework.domain.entity import Homework, HomeworkSubmission, SubmissionType
from app.homework.infrastructure.homework_assignee_repository import (
    AssigneeUserInfo,
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.reminder.application.scanners.homework_scanner import HomeworkTaskScanner


def test_scanner_includes_partially_submitted_homework():
    """Kiểm tra học sinh mới làm 1/2 bài coding thì scanner KHÔNG bỏ qua mà tạo reminder."""
    mock_hw_repo = MagicMock(spec=HomeworkRepository)
    mock_assignee_repo = MagicMock(spec=HomeworkAssigneeRepository)
    mock_sub_repo = MagicMock(spec=HomeworkSubmissionRepository)

    now = datetime(2026, 11, 15, 10, 0, 0, tzinfo=UTC)
    deadline = now + timedelta(hours=4)  # Khớp mốc OFFSET_4H (3.5h - 4.5h)

    hw = Homework(
        id=1,
        title="Bài tập có 2 bài con",
        requires_coding=True,
        requires_game=False,
    )
    mock_hw_repo.get_all.return_value = [hw]

    assignee = AssigneeUserInfo(
        user_id=10,
        deadline=deadline,
        name="Test User",
        avatar_url=None,
    )
    mock_assignee_repo.get_assignees_with_user_info.return_value = [assignee]

    # Học sinh chỉ nộp 1 bài ex-1
    sub = HomeworkSubmission(
        id=1,
        homework_id=1,
        user_id=10,
        submission_type=SubmissionType.CODING,
        exercise_id="ex-1",
        is_passed=True,
        submitted_at=now - timedelta(hours=1),
    )
    mock_sub_repo.get_submissions_by_user.return_value = [sub]
    mock_sub_repo.get_required_exercise_ids_map.return_value = {1: {"ex-1", "ex-2"}}

    scanner = HomeworkTaskScanner(
        homework_repo=mock_hw_repo,
        homework_assignee_repo=mock_assignee_repo,
        homework_submission_repo=mock_sub_repo,
    )

    candidates = scanner.scan_pending_tasks(now)

    assert len(candidates) == 1
    assert candidates[0].task_id == 1
    assert candidates[0].user_id == 10
