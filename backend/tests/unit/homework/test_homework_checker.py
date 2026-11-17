"""
Unit tests for CheckOverdueHomeworkUseCase running on In-Memory Fake Repositories (Zero-Mock).
Verifies overdue detection, multi-exercise progress, per-assignee independent deadlines,
resubmission after deadline fairness, and clear plain-text late vs uncompleted reasons.
"""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.homework.application import CheckOverdueHomeworkUseCase
from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
from app.homework.domain.entity import CodingHomeworkSubmission, Homework
from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    HomeworkOverdueDetected,
)
from tests.fixtures.homework_fixtures import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    SpyEventBus,
    make_exercise,
)


@pytest.mark.asyncio
async def test_check_overdue_homework_publishes_event(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    spy_event_bus: SpyEventBus,
):
    """User 101 nộp đúng hạn -> không phạt; User 102 chưa nộp -> phạt."""
    deadline_dt = datetime(2026, 9, 25, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    hw = in_memory_homework_repo.save(
        Homework(
            id=1,
            title="Bài tập Python OOP",
            slug="python-oop",
            requires_coding=True,
            requires_game=False,
        )
    )
    in_memory_assignee_repo.set_homework_info(
        1, title=hw.title, requires_coding=True, requires_game=False, slug="python-oop"
    )
    in_memory_assignee_repo.set_assignees(
        1,
        [
            AssigneeUserInfo(user_id=101, name="User 101", avatar_url=None, deadline=deadline_dt),
            AssigneeUserInfo(user_id=102, name="User 102", avatar_url=None, deadline=deadline_dt),
        ],
        default_deadline=deadline_dt,
    )
    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=1,
            user_id=101,
            exercise_id="default",
            submitted_at=datetime(2026, 9, 25, 20, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
            is_passed=True,
        )
    )

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 9, 25))
    assert count == 1
    overdue_events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(overdue_events) == 1
    assert overdue_events[0].user_id == 102
    assert overdue_events[0].homework_id == 1


@pytest.mark.asyncio
async def test_check_overdue_multi_exercise_partial_submission_flags_overdue(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    spy_event_bus: SpyEventBus,
):
    """Học viên chỉ nộp 1/2 bài tập con chính thức bị tính là quá hạn bài tập coding."""
    deadline_dt = datetime(2026, 10, 1, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(
            id=2,
            title="Lesson 2: Multitask",
            slug="lesson-2-multitask",
            requires_coding=True,
            requires_game=False,
        )
    )
    in_memory_assignee_repo.set_homework_info(
        2, title="Lesson 2: Multitask", requires_coding=True, requires_game=False, slug="lesson-2-multitask"
    )
    in_memory_assignee_repo.set_assignees(
        2,
        [AssigneeUserInfo(user_id=201, name="User 201", avatar_url=None, deadline=deadline_dt)],
        default_deadline=deadline_dt,
    )
    in_memory_exercise_repo.sync_exercises(
        2, [make_exercise(2, "ex-1", "Ex 1", 1), make_exercise(2, "ex-2", "Ex 2", 2)]
    )

    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=2,
            user_id=201,
            exercise_id="ex-1",
            submitted_at=datetime(2026, 10, 1, 10, 0, tzinfo=UTC),
            is_passed=True,
        )
    )

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 10, 1))
    assert count == 1
    events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events) == 1
    assert events[0].user_id == 201
    assert "bài tập coding" in events[0].reason.lower()


@pytest.mark.asyncio
async def test_check_overdue_resubmit_after_deadline_does_not_penalize_on_time_student(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    spy_event_bus: SpyEventBus,
):
    """US5: Học viên nộp đạt đủ 2/2 bài TRƯỚC hạn, sau hạn nộp lại cải thiện/trượt -> KHÔNG bị phạt."""
    deadline_dt = datetime(2026, 10, 1, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(
            id=3,
            title="Lesson 3: Multitask Complete",
            slug="lesson-3-multitask",
            requires_coding=True,
            requires_game=False,
        )
    )
    in_memory_assignee_repo.set_homework_info(
        3, title="Lesson 3: Multitask Complete", requires_coding=True, requires_game=False, slug="lesson-3-multitask"
    )
    in_memory_assignee_repo.set_assignees(
        3,
        [AssigneeUserInfo(user_id=301, name="User 301", avatar_url=None, deadline=deadline_dt)],
        default_deadline=deadline_dt,
    )
    in_memory_exercise_repo.sync_exercises(
        3, [make_exercise(3, "ex-1", "Ex 1", 1), make_exercise(3, "ex-2", "Ex 2", 2)]
    )

    in_memory_submission_repo.add_submissions(
        [
            CodingHomeworkSubmission.create_coding(
                homework_id=3,
                user_id=301,
                exercise_id="ex-1",
                external_submission_id="sub-1",
                submitted_at=datetime(2026, 10, 1, 20, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
                is_passed=True,
            ),
            CodingHomeworkSubmission.create_coding(
                homework_id=3,
                user_id=301,
                exercise_id="ex-2",
                external_submission_id="sub-2",
                submitted_at=datetime(2026, 10, 1, 21, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
                is_passed=True,
            ),
            # Nộp lại ex-2 sau hạn 5 tiếng
            CodingHomeworkSubmission.create_coding(
                homework_id=3,
                user_id=301,
                exercise_id="ex-2",
                external_submission_id="sub-3",
                submitted_at=datetime(2026, 10, 2, 5, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
                is_passed=False,
            ),
        ]
    )

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 10, 1))
    assert count == 0
    assert len(spy_event_bus.published_events) == 0


@pytest.mark.asyncio
async def test_check_overdue_homework_default_target_date_delays_2_days(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    spy_event_bus: SpyEventBus,
):
    """Khi target_date is None, tự động quét đúng ngày (today_vn - 2 ngày)."""
    now_vn = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    target_date = now_vn.date() - timedelta(days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS)
    today_date = now_vn.date()

    target_dl = datetime.combine(target_date, datetime.min.time(), tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    today_dl = datetime.combine(today_date, datetime.min.time(), tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(id=4, title="Lesson Delay", slug="lesson-delay", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.set_homework_info(4, "Lesson Delay", True, False, "lesson-delay")
    in_memory_assignee_repo.set_assignees(
        4,
        [
            AssigneeUserInfo(user_id=401, name="User 401", avatar_url=None, deadline=target_dl),
            AssigneeUserInfo(user_id=402, name="User 402", avatar_url=None, deadline=today_dl),
        ],
    )
    in_memory_assignee_repo.set_custom_deadline(4, 401, target_dl)
    in_memory_assignee_repo.set_custom_deadline(4, 402, today_dl)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute()
    assert count == 1
    events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events) == 1
    assert events[0].user_id == 401


@pytest.mark.asyncio
async def test_check_overdue_homework_flags_late_full_submission_with_clear_reason(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    spy_event_bus: SpyEventBus,
):
    """Học viên hoàn thành 100% SAU deadline vẫn tạo vi phạm với lý do plain-text 'Nộp bài tập trễ hạn'."""
    deadline_dt = datetime(2026, 10, 25, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(id=10, title="Bài tập SQL", slug="sql-basics", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.set_homework_info(10, "Bài tập SQL", True, False, "sql-basics")
    in_memory_assignee_repo.set_assignees(
        10,
        [AssigneeUserInfo(user_id=501, name="User 501", avatar_url=None, deadline=deadline_dt)],
        default_deadline=deadline_dt,
    )
    in_memory_exercise_repo.sync_exercises(10, [make_exercise(10, "ex-sql", "SQL 1", 1)])
    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=10,
            user_id=501,
            exercise_id="ex-sql",
            submitted_at=datetime(2026, 10, 26, 1, 0, tzinfo=UTC),
            is_passed=True,
        )
    )

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 10, 25))
    assert count == 1
    events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events) == 1
    assert events[0].user_id == 501
    assert events[0].reason == "Nộp bài tập trễ hạn (Bài tập SQL)"


@pytest.mark.asyncio
async def test_check_overdue_homework_per_assignee_independent_deadlines(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    spy_event_bus: SpyEventBus,
):
    """Hai học viên cùng một bài tập có deadline khác nhau được quét hoàn toàn độc lập."""
    dl_a = datetime(2026, 11, 10, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    dl_b = datetime(2026, 11, 14, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(id=1, title="Python Lesson", slug="python-lesson", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.set_homework_info(1, "Python Lesson", True, False, "python-lesson")
    in_memory_assignee_repo.set_assignees(
        1,
        [
            AssigneeUserInfo(user_id=10, name="User 10", avatar_url=None, deadline=dl_a),
            AssigneeUserInfo(user_id=20, name="User 20", avatar_url=None, deadline=dl_b),
        ],
    )
    in_memory_assignee_repo.set_custom_deadline(1, 10, dl_a)
    in_memory_assignee_repo.set_custom_deadline(1, 20, dl_b)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        event_bus=spy_event_bus,  # type: ignore
    )

    count_10 = await use_case.execute(target_date=date(2026, 11, 10))
    assert count_10 == 1
    assert spy_event_bus.get_events_of_type(HomeworkOverdueDetected)[0].user_id == 10

    spy_event_bus.clear()
    count_14 = await use_case.execute(target_date=date(2026, 11, 14))
    assert count_14 == 1
    assert spy_event_bus.get_events_of_type(HomeworkOverdueDetected)[0].user_id == 20
