"""Unit tests for GetUserHomeworksUseCase ensuring proper status evaluation with sub-exercises."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.homework.application.get_user_homeworks_use_case import GetUserHomeworksUseCase
from app.homework.domain.entity import Homework, HomeworkSubmission, SubmissionType
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)


@pytest.mark.asyncio
async def test_get_user_homeworks_partial_coding_returns_unsubmitted():
    """Kiểm tra học sinh mới làm 1/2 bài coding thì is_submitted=False và coding_status=PARTIALLY_SUBMITTED."""
    mock_hw_repo = MagicMock(spec=HomeworkRepository)
    mock_sub_repo = MagicMock(spec=HomeworkSubmissionRepository)
    mock_assignee_repo = MagicMock(spec=HomeworkAssigneeRepository)

    hw = Homework(
        id=1,
        title="Đại số tuyến tính",
        requires_coding=True,
        requires_game=False,
    )
    mock_hw_repo.get_assigned_to_user_paged.return_value = ([hw], 1)

    future_dl = datetime.now(UTC) + timedelta(days=2)
    mock_assignee_repo.get_user_deadlines_for_homeworks.return_value = {1: future_dl}

    # Học sinh chỉ nộp ex-1
    sub = HomeworkSubmission(
        id=1,
        homework_id=1,
        user_id=10,
        submission_type=SubmissionType.CODING,
        exercise_id="ex-1",
        is_passed=True,
        submitted_at=datetime.now(UTC),
    )
    mock_sub_repo.get_user_submissions_for_homeworks.return_value = [sub]

    # Cả bài học có 2 bài con: ex-1 và ex-2
    mock_sub_repo.get_required_exercise_ids_map.return_value = {1: {"ex-1", "ex-2"}}

    use_case = GetUserHomeworksUseCase(
        homework_repo=mock_hw_repo,
        homework_submission_repo=mock_sub_repo,
        homework_assignee_repo=mock_assignee_repo,
    )

    responses, total = await use_case.execute(user_id=10, page=1, page_size=20)

    assert total == 1
    assert len(responses) == 1
    item = responses[0]
    assert item.id == 1
    assert item.is_submitted is False
    assert item.coding_status == "PARTIALLY_SUBMITTED"
    assert item.total_coding_required == 2
    assert item.total_coding_completed == 1
    assert "Còn 1/2 bài tập Coding" in item.uncompleted_items


@pytest.mark.asyncio
async def test_get_user_homeworks_full_coding_returns_submitted():
    """Kiểm tra học sinh làm đủ cả 2 bài coding thì is_submitted=True và coding_status=COMPLETED."""
    mock_hw_repo = MagicMock(spec=HomeworkRepository)
    mock_sub_repo = MagicMock(spec=HomeworkSubmissionRepository)
    mock_assignee_repo = MagicMock(spec=HomeworkAssigneeRepository)

    hw = Homework(
        id=1,
        title="Đại số tuyến tính",
        requires_coding=True,
        requires_game=False,
    )
    mock_hw_repo.get_assigned_to_user_paged.return_value = ([hw], 1)

    future_dl = datetime.now(UTC) + timedelta(days=2)
    mock_assignee_repo.get_user_deadlines_for_homeworks.return_value = {1: future_dl}

    # Học sinh nộp cả ex-1 và ex-2
    subs = [
        HomeworkSubmission(
            id=1,
            homework_id=1,
            user_id=10,
            submission_type=SubmissionType.CODING,
            exercise_id="ex-1",
            is_passed=True,
            submitted_at=datetime.now(UTC),
        ),
        HomeworkSubmission(
            id=2,
            homework_id=1,
            user_id=10,
            submission_type=SubmissionType.CODING,
            exercise_id="ex-2",
            is_passed=True,
            submitted_at=datetime.now(UTC),
        ),
    ]
    mock_sub_repo.get_user_submissions_for_homeworks.return_value = subs
    mock_sub_repo.get_required_exercise_ids_map.return_value = {1: {"ex-1", "ex-2"}}

    use_case = GetUserHomeworksUseCase(
        homework_repo=mock_hw_repo,
        homework_submission_repo=mock_sub_repo,
        homework_assignee_repo=mock_assignee_repo,
    )

    responses, total = await use_case.execute(user_id=10, page=1, page_size=20)

    assert total == 1
    assert len(responses) == 1
    item = responses[0]
    assert item.id == 1
    assert item.is_submitted is True
    assert item.coding_status == "COMPLETED"
    assert item.total_coding_required == 2
    assert item.total_coding_completed == 2
    assert len(item.uncompleted_items) == 0
