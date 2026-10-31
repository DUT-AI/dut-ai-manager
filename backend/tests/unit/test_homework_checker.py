from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.homework.application import CheckOverdueHomeworkUseCase
from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
from app.homework.domain.entity import (
    HomeworkSubmission as HomeworkSubmissionEntity,
    SubmissionType,
)
from app.homework.domain.value_objects import (
    DueHomeworkAssignment,
    HomeworkOverdueDetected,
)


@pytest.mark.asyncio
async def test_check_overdue_homework_publishes_event():
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    deadline_dt = datetime(2026, 9, 25, 23, 59, tzinfo=UTC)
    assignee_repo = MagicMock()
    assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=1,
            user_id=101,
            homework_title="Bài tập Python OOP",
            deadline=deadline_dt,
            requires_coding=True,
            requires_game=False,
        ),
        DueHomeworkAssignment(
            homework_id=1,
            user_id=102,
            homework_title="Bài tập Python OOP",
            deadline=deadline_dt,
            requires_coding=True,
            requires_game=False,
        ),
    ]

    # Không có sub-exercises con
    submission_repo.get_submissions_by_homework.return_value = []
    # User 101 có bài nộp hợp lệ trước deadline; User 102 không có
    submission_repo.has_valid_submission.side_effect = (
        lambda h_id, u_id, s_type, deadline: u_id == 101
    )
    quiz_api = MagicMock()
    quiz_api.get_lesson_exercises = AsyncMock(return_value=None)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
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

    deadline_dt = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)
    assignee_repo = MagicMock()
    assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=2,
            user_id=201,
            homework_title="Lesson 2: Multitask",
            deadline=deadline_dt,
            requires_coding=True,
            requires_game=False,
        )
    ]

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
    quiz_api = MagicMock()
    quiz_api.get_lesson_exercises = AsyncMock(return_value=None)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
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

    deadline_dt = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)
    assignee_repo = MagicMock()
    assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=3,
            user_id=301,
            homework_title="Lesson 3: Multitask Complete",
            deadline=deadline_dt,
            requires_coding=True,
            requires_game=False,
        )
    ]

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
    quiz_api = MagicMock()
    quiz_api.get_lesson_exercises = AsyncMock(return_value=None)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 10, 1))

    assert count == 0
    assert not event_bus.publish.called


@pytest.mark.asyncio
async def test_check_overdue_homework_default_target_date_delays_2_days():
    """Khi target_date is None, hệ thống tự động quét ngày (today - 2 ngày)."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    assignee_repo = MagicMock()
    assignee_repo.get_by_deadline_date.return_value = []
    event_bus = MagicMock()
    quiz_api = MagicMock()
    quiz_api.get_lesson_exercises = AsyncMock(return_value=None)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
        event_bus=event_bus,
    )

    now_vn = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    expected_target_date = now_vn.date() - timedelta(
        days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
    )

    await use_case.execute()

    assignee_repo.get_by_deadline_date.assert_called_once_with(expected_target_date)


@pytest.mark.asyncio
async def test_check_overdue_homework_flags_late_submission():
    """Học viên nộp sau deadline (không có submission <= deadline trong DB) vẫn bị tạo vi phạm."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    deadline_dt = datetime(2026, 10, 25, 23, 59, tzinfo=UTC)
    assignee_repo = MagicMock()
    assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=10,
            user_id=501,
            homework_title="Bài tập SQL",
            deadline=deadline_dt,
            requires_coding=True,
            requires_game=False,
        )
    ]

    # Không có sub-exercises
    submission_repo.get_submissions_by_homework.return_value = []
    # has_valid_submission lọc theo submitted_at <= deadline, trả False vì user nộp trễ hoặc chưa nộp
    submission_repo.has_valid_submission.return_value = False
    quiz_api = MagicMock()
    quiz_api.get_lesson_exercises = AsyncMock(return_value=None)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 10, 25))

    assert count == 1
    assert event_bus.publish.called
    published = event_bus.publish.call_args[0][0]
    assert isinstance(published, HomeworkOverdueDetected)
    assert published.user_id == 501


@pytest.mark.asyncio
async def test_check_overdue_homework_per_assignee_independent_deadlines():
    """Kiểm tra hai học viên trong cùng một bài tập có deadline khác nhau được quét hoàn toàn độc lập."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    submission_repo.get_submissions_by_homework.return_value = []
    submission_repo.has_valid_submission.return_value = False
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()
    assignee_repo = MagicMock()
    quiz_api = MagicMock()
    quiz_api.get_lesson_exercises = AsyncMock(return_value=None)

    dl_a = datetime(2026, 11, 10, 23, 59, tzinfo=UTC)
    dl_b = datetime(2026, 11, 14, 23, 59, tzinfo=UTC)

    # Khi quét ngày 10: Chỉ có học viên A
    assignee_repo.get_by_deadline_date.side_effect = lambda t_date: (
        [
            DueHomeworkAssignment(
                homework_id=1,
                user_id=10,
                homework_title="Python Lesson",
                deadline=dl_a,
                requires_coding=True,
                requires_game=False,
            )
        ]
        if t_date == date(2026, 11, 10)
        else [
            DueHomeworkAssignment(
                homework_id=1,
                user_id=20,
                homework_title="Python Lesson",
                deadline=dl_b,
                requires_coding=True,
                requires_game=False,
            )
        ]
        if t_date == date(2026, 11, 14)
        else []
    )

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
        event_bus=event_bus,
    )

    # 1. Quét ngày 10: Chỉ học viên 10 bị phạt
    count_10 = await use_case.execute(target_date=date(2026, 11, 10))
    assert count_10 == 1
    assert event_bus.publish.call_args[0][0].user_id == 10

    # 2. Quét ngày 14: Chỉ học viên 20 bị phạt
    event_bus.publish.reset_mock()
    count_14 = await use_case.execute(target_date=date(2026, 11, 14))
    assert count_14 == 1
    assert event_bus.publish.call_args[0][0].user_id == 20


@pytest.mark.asyncio
async def test_check_overdue_homework_uses_quiz_api_exercises():
    """Hệ thống lấy danh mục bài con trực tiếp từ Quiz API để đối soát hoàn thành coding."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    assignee_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()
    quiz_api = MagicMock()

    deadline_dt = datetime(2026, 11, 1, 23, 59, tzinfo=UTC)
    assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=20,
            user_id=1001,
            homework_title="Bài tập thuật toán Quiz",
            deadline=deadline_dt,
            requires_coding=True,
            requires_game=False,
            slug="algo-lesson-01",
        )
    ]

    # Quiz API trả về 3 bài tập con
    quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[
            {"id": "ex_1", "title": "Bài 1"},
            {"id": "ex_2", "title": "Bài 2"},
            {"id": "ex_3", "title": "Bài 3"},
        ]
    )

    # User 1001 mới chỉ nộp ex_1 và ex_2, thiếu ex_3
    submission_repo.get_submitted_exercise_ids.return_value = {"ex_1", "ex_2"}

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 11, 1))

    # Thiếu bài 3 nên phải phát event overdue
    assert count == 1
    assert event_bus.publish.called
    published = event_bus.publish.call_args[0][0]
    assert isinstance(published, HomeworkOverdueDetected)
    assert published.user_id == 1001
    assert "bài tập coding" in published.reason


@pytest.mark.asyncio
async def test_check_overdue_homework_fallbacks_when_quiz_api_fails():
    """Khi Quiz API bị lỗi mạng hoặc timeout, hệ thống tự động fallback dùng danh sách từ submissions trong DB."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    assignee_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()
    quiz_api = MagicMock()

    deadline_dt = datetime(2026, 11, 1, 23, 59, tzinfo=UTC)
    assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=25,
            user_id=1002,
            homework_title="Bài tập Fallback",
            deadline=deadline_dt,
            requires_coding=True,
            requires_game=False,
            slug="lesson-fallback",
        )
    ]

    # Quiz API ném lỗi
    quiz_api.get_lesson_exercises = AsyncMock(side_effect=Exception("Quiz API timeout"))

    # Fallback submissions trong DB có ex_alpha
    sub = MagicMock(spec=HomeworkSubmissionEntity)
    sub.exercise_id = "ex_alpha"
    sub.submission_type = SubmissionType.CODING
    submission_repo.get_submissions_by_homework.return_value = [sub]

    # User 1002 đã nộp đủ ex_alpha
    submission_repo.get_submitted_exercise_ids.return_value = {"ex_alpha"}

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        quiz_api=quiz_api,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 11, 1))

    # User đã hoàn thành bài ex_alpha nên không bị phạt
    assert count == 0
    assert not event_bus.publish.called
