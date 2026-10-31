from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.homework.application import CheckOverdueHomeworkUseCase
from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
from app.homework.domain.entity import (
    Homework as HomeworkEntity,
    HomeworkSubmission as HomeworkSubmissionEntity,
    SubmissionType,
)
from app.homework.domain.value_objects import HomeworkOverdueDetected


@pytest.mark.asyncio
async def test_check_overdue_homework_publishes_event():
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    # Create dummy homework due today with assignee user 101 and 102
    hw = HomeworkEntity(
        id=1,
        title="Bài tập Python OOP",
        slug="python-oop",
        deadline=datetime(2026, 9, 25, 23, 59, tzinfo=UTC),
        link="https://quiz.example.com/homeworks/python-oop",
        requires_coding=True,
    )
    homework_repo.get_by_deadline_date.return_value = [hw]
    assignee_repo = MagicMock()
    assignee_repo.get_assigned_user_ids.return_value = {101, 102}

    # Không có sub-exercises con
    submission_repo.get_submissions_by_homework.return_value = []
    # User 101 có bài nộp hợp lệ trước deadline; User 102 không có
    submission_repo.has_valid_submission.side_effect = (
        lambda h_id, u_id, s_type, deadline: u_id == 101
    )

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 9, 25))

    # User 102 should trigger HomeworkOverdueDetected event
    assert count == 1
    assert event_bus.publish.called

    published_events = [call[0][0] for call in event_bus.publish.call_args_list]
    overdue_events = [
        e for e in published_events if isinstance(e, HomeworkOverdueDetected)
    ]
    assert len(overdue_events) == 1
    assert overdue_events[0].user_id == 102
    assert overdue_events[0].homework_id == 1


@pytest.mark.asyncio
async def test_check_overdue_multi_exercise_partial_submission_flags_overdue():
    """Học viên chỉ nộp 1/2 bài tập con sẽ bị tính là quá hạn bài tập coding."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    hw = HomeworkEntity(
        id=2,
        title="Lesson 2: Multitask",
        slug="lesson-2-multi",
        deadline=datetime(2026, 10, 1, 23, 59, tzinfo=UTC),
        link="https://quiz.example.com/homeworks/lesson-2-multi",
        requires_coding=True,
    )
    homework_repo.get_by_deadline_date.return_value = [hw]
    assignee_repo = MagicMock()
    assignee_repo.get_assigned_user_ids.return_value = {201}

    # Có 2 bài tập con: ex-1 và ex-2
    sub1 = MagicMock(spec=HomeworkSubmissionEntity)
    sub1.exercise_id = "ex-1"
    sub1.submission_type = SubmissionType.CODING
    sub2 = MagicMock(spec=HomeworkSubmissionEntity)
    sub2.exercise_id = "ex-2"
    sub2.submission_type = SubmissionType.CODING
    submission_repo.get_submissions_by_homework.return_value = [sub1, sub2]

    # User 201 chỉ nộp ex-1
    submission_repo.get_submitted_exercise_ids.return_value = {"ex-1"}

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 10, 1))

    assert count == 1
    published_events = [call[0][0] for call in event_bus.publish.call_args_list]
    overdue_events = [
        e for e in published_events if isinstance(e, HomeworkOverdueDetected)
    ]
    assert len(overdue_events) == 1
    assert overdue_events[0].user_id == 201
    assert "bài tập coding" in overdue_events[0].reason


@pytest.mark.asyncio
async def test_check_overdue_multi_exercise_full_submission_passes():
    """Học viên nộp đủ 2/2 bài tập con trong DB không bị phạt."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    hw = HomeworkEntity(
        id=3,
        title="Lesson 3: Multitask Complete",
        slug="lesson-3-multi",
        deadline=datetime(2026, 10, 1, 23, 59, tzinfo=UTC),
        link="https://quiz.example.com/homeworks/lesson-3-multi",
        requires_coding=True,
    )
    homework_repo.get_by_deadline_date.return_value = [hw]
    assignee_repo = MagicMock()
    assignee_repo.get_assigned_user_ids.return_value = {301}

    # Có 2 bài tập con: ex-1 và ex-2
    sub1 = MagicMock(spec=HomeworkSubmissionEntity)
    sub1.exercise_id = "ex-1"
    sub1.submission_type = SubmissionType.CODING
    sub2 = MagicMock(spec=HomeworkSubmissionEntity)
    sub2.exercise_id = "ex-2"
    sub2.submission_type = SubmissionType.CODING
    submission_repo.get_submissions_by_homework.return_value = [sub1, sub2]

    # User 301 đã nộp cả ex-1 và ex-2
    submission_repo.get_submitted_exercise_ids.return_value = {"ex-1", "ex-2"}

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 10, 1))

    assert count == 0
    assert not event_bus.publish.called


@pytest.mark.asyncio
async def test_check_overdue_homework_default_target_date_delays_2_days():
    """Khi target_date is None, hệ thống tự động quét ngày (today - 2 ngày)."""
    homework_repo = MagicMock()
    homework_repo.get_by_deadline_date.return_value = []
    submission_repo = MagicMock()
    assignee_repo = MagicMock()
    event_bus = MagicMock()

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        event_bus=event_bus,
    )

    now_vn = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    expected_target_date = now_vn.date() - timedelta(days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS)

    await use_case.execute()

    homework_repo.get_by_deadline_date.assert_called_once_with(expected_target_date)


@pytest.mark.asyncio
async def test_check_overdue_homework_flags_late_submission():
    """Học viên nộp sau deadline (không có submission <= deadline trong DB) vẫn bị tạo vi phạm."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    deadline_dt = datetime(2026, 10, 25, 23, 59, tzinfo=UTC)
    hw = HomeworkEntity(
        id=10,
        title="Bài tập SQL",
        slug="sql-basics",
        deadline=deadline_dt,
        link="https://quiz.example.com/homeworks/sql-basics",
        requires_coding=True,
    )
    homework_repo.get_by_deadline_date.return_value = [hw]
    assignee_repo = MagicMock()
    assignee_repo.get_assigned_user_ids.return_value = {501}

    # Không có sub-exercises
    submission_repo.get_submissions_by_homework.return_value = []
    # has_valid_submission lọc theo submitted_at <= deadline, trả False vì user nộp trễ hoặc chưa nộp
    submission_repo.has_valid_submission.return_value = False

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 10, 25))

    assert count == 1
    assert event_bus.publish.called
    published = event_bus.publish.call_args[0][0]
    assert isinstance(published, HomeworkOverdueDetected)
    assert published.user_id == 501
