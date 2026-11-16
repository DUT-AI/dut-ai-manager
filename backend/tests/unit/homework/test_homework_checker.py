"""
Unit tests for CheckOverdueHomeworkUseCase running on In-Memory Fake Repositories (Zero-Mock).
Verifies overdue detection, multi-exercise progress, per-assignee independent deadlines,
and fallback behavior completely in RAM without database or MagicMock.
"""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.homework.application import (
    CheckOverdueHomeworkUseCase,
    HomeworkExerciseResolver,
)
from app.homework.domain.constants import HOMEWORK_VIOLATION_CHECK_DELAY_DAYS
from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    Homework,
)
from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    HomeworkOverdueDetected,
)
from tests.fixtures.homework_fixtures import (
    FakeQuizApiClient,
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    SpyEventBus,
)


@pytest.mark.asyncio
async def test_check_overdue_homework_publishes_event(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 1: Quét hạn bài tập phát hiện học viên chưa hoàn thành bài tập:
    - User 101 có bài nộp hợp lệ trước deadline -> Không bị phạt.
    - User 102 chưa nộp bài -> Phát hiện vi phạm và phát sự kiện HomeworkOverdueDetected.
    """
    deadline_dt = datetime(2026, 9, 25, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    # 1. Seed homework
    hw = in_memory_homework_repo.save(
        Homework(
            id=1,
            title="Bài tập Python OOP",
            slug="python-oop",
            requires_coding=True,
            requires_game=False,
        )
    )

    # 2. Seed assignees
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

    # 3. User 101 có bài nộp hợp lệ trước deadline (20:00 VN < 23:59 VN); User 102 không có
    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=1,
            user_id=101,
            exercise_id="default",
            submitted_at=datetime(2026, 9, 25, 20, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
            is_passed=True,
        )
    )

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 9, 25))

    # User 102 phát hiện quá hạn
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
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 2: Học viên chỉ nộp 1/2 bài tập con sẽ bị tính là quá hạn bài tập coding.
    """
    deadline_dt = datetime(2026, 10, 1, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    # Seed homework có 2 bài tập con
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

    # Fake Quiz API trả về 2 bài tập con: ex-1 và ex-2
    fake_quiz_api.set_lesson_exercises(
        "lesson-2-multitask",
        [{"id": "ex-1", "title": "Ex 1"}, {"id": "ex-2", "title": "Ex 2"}],
    )

    # User 201 chỉ nộp ex-1
    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=2,
            user_id=201,
            exercise_id="ex-1",
            submitted_at=datetime(2026, 10, 1, 20, 0, tzinfo=UTC),
            is_passed=True,
        )
    )

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 10, 1))

    assert count == 1
    overdue_events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(overdue_events) == 1
    assert overdue_events[0].user_id == 201
    assert "bài tập coding" in overdue_events[0].reason.lower()


@pytest.mark.asyncio
async def test_check_overdue_multi_exercise_full_submission_passes(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 3: Học viên nộp đủ 2/2 bài tập con không bị phạt.
    """
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

    fake_quiz_api.set_lesson_exercises(
        "lesson-3-multitask",
        [{"id": "ex-1", "title": "Ex 1"}, {"id": "ex-2", "title": "Ex 2"}],
    )

    # User 301 đã nộp cả ex-1 và ex-2 trước deadline (20:00 và 21:00 VN < 23:59 VN)
    in_memory_submission_repo.add_submissions([
        CodingHomeworkSubmission.create_coding(
            homework_id=3,
            user_id=301,
            exercise_id="ex-1",
            submitted_at=datetime(2026, 10, 1, 20, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
            is_passed=True,
        ),
        CodingHomeworkSubmission.create_coding(
            homework_id=3,
            user_id=301,
            exercise_id="ex-2",
            submitted_at=datetime(2026, 10, 1, 21, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
            is_passed=True,
        ),
    ])

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
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
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 4: Khi target_date is None, hệ thống tự động quét đúng ngày (today_vn - 2 ngày).
    """
    now_vn = datetime.now(UTC).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
    target_date = now_vn.date() - timedelta(days=HOMEWORK_VIOLATION_CHECK_DELAY_DAYS)
    today_date = now_vn.date()

    target_dl = datetime.combine(target_date, datetime.min.time(), tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    today_dl = datetime.combine(today_date, datetime.min.time(), tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(id=4, title="Lesson Delay", slug="lesson-delay", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.set_homework_info(4, "Lesson Delay", True, False, "lesson-delay")

    # User 401 có deadline vào đúng target_date (2 ngày trước); User 402 có deadline hôm nay
    in_memory_assignee_repo.set_assignees(
        4,
        [
            AssigneeUserInfo(user_id=401, name="User 401", avatar_url=None, deadline=target_dl),
            AssigneeUserInfo(user_id=402, name="User 402", avatar_url=None, deadline=today_dl),
        ],
    )
    in_memory_assignee_repo.set_custom_deadline(4, 401, target_dl)
    in_memory_assignee_repo.set_custom_deadline(4, 402, today_dl)

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    # Chạy mặc định không truyền target_date
    count = await use_case.execute()

    # Chỉ user 401 (deadline cách 2 ngày) bị quét và phát hiện quá hạn
    assert count == 1
    events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events) == 1
    assert events[0].user_id == 401


@pytest.mark.asyncio
async def test_check_overdue_homework_flags_late_submission(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 5: Học viên nộp sau deadline vẫn bị tạo vi phạm quá hạn.
    """
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

    # User 501 nộp trễ sau deadline (1h sáng ngày hôm sau)
    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=10,
            user_id=501,
            exercise_id="default",
            submitted_at=datetime(2026, 10, 26, 1, 0, tzinfo=UTC),
            is_passed=True,
        )
    )

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 10, 25))

    assert count == 1
    events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events) == 1
    assert events[0].user_id == 501


@pytest.mark.asyncio
async def test_check_overdue_homework_per_assignee_independent_deadlines(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 6: Hai học viên trong cùng một bài tập có deadline khác nhau được quét hoàn toàn độc lập.
    """
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

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    # 1. Quét ngày 10: Chỉ học viên 10 bị phạt
    count_10 = await use_case.execute(target_date=date(2026, 11, 10))
    assert count_10 == 1
    events_10 = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events_10) == 1
    assert events_10[0].user_id == 10

    # 2. Quét ngày 14: Chỉ học viên 20 bị phạt
    spy_event_bus.clear()
    count_14 = await use_case.execute(target_date=date(2026, 11, 14))
    assert count_14 == 1
    events_14 = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events_14) == 1
    assert events_14[0].user_id == 20


@pytest.mark.asyncio
async def test_check_overdue_homework_uses_quiz_api_exercises(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 7: Hệ thống lấy danh mục bài con trực tiếp từ Quiz API để đối soát hoàn thành coding.
    """
    deadline_dt = datetime(2026, 11, 1, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(
            id=20,
            title="Bài tập thuật toán Quiz",
            slug="algo-lesson-01",
            requires_coding=True,
            requires_game=False,
        )
    )
    in_memory_assignee_repo.set_homework_info(
        20,
        title="Bài tập thuật toán Quiz",
        requires_coding=True,
        requires_game=False,
        slug="algo-lesson-01",
    )
    in_memory_assignee_repo.set_assignees(
        20,
        [AssigneeUserInfo(user_id=1001, name="User 1001", avatar_url=None, deadline=deadline_dt)],
        default_deadline=deadline_dt,
    )

    # Quiz API trả về 3 bài tập con: ex_1, ex_2, ex_3
    fake_quiz_api.set_lesson_exercises(
        "algo-lesson-01",
        [
            {"id": "ex_1", "title": "Bài 1"},
            {"id": "ex_2", "title": "Bài 2"},
            {"id": "ex_3", "title": "Bài 3"},
        ],
    )

    # User 1001 mới chỉ nộp ex_1 và ex_2, thiếu ex_3
    in_memory_submission_repo.add_submissions([
        CodingHomeworkSubmission.create_coding(
            homework_id=20,
            user_id=1001,
            exercise_id="ex_1",
            submitted_at=datetime(2026, 11, 1, 20, 0, tzinfo=UTC),
            is_passed=True,
        ),
        CodingHomeworkSubmission.create_coding(
            homework_id=20,
            user_id=1001,
            exercise_id="ex_2",
            submitted_at=datetime(2026, 11, 1, 21, 0, tzinfo=UTC),
            is_passed=True,
        ),
    ])

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 11, 1))

    # Thiếu bài 3 nên phải phát event overdue
    assert count == 1
    events = spy_event_bus.get_events_of_type(HomeworkOverdueDetected)
    assert len(events) == 1
    assert events[0].user_id == 1001
    assert "bài tập coding" in events[0].reason.lower()


@pytest.mark.asyncio
async def test_check_overdue_homework_fallbacks_when_quiz_api_fails(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
    spy_event_bus: SpyEventBus,
):
    """
    Test 8: Khi Quiz API bị lỗi mạng hoặc timeout, hệ thống tự động fallback dùng danh sách từ submissions trong RAM.
    """
    deadline_dt = datetime(2026, 11, 1, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.save(
        Homework(
            id=25,
            title="Bài tập Fallback",
            slug="lesson-fallback",
            requires_coding=True,
            requires_game=False,
        )
    )
    in_memory_assignee_repo.set_homework_info(
        25,
        title="Bài tập Fallback",
        requires_coding=True,
        requires_game=False,
        slug="lesson-fallback",
    )
    in_memory_assignee_repo.set_assignees(
        25,
        [AssigneeUserInfo(user_id=1002, name="User 1002", avatar_url=None, deadline=deadline_dt)],
        default_deadline=deadline_dt,
    )

    # Quiz API bị lỗi
    fake_quiz_api.should_fail = True

    # Submissions đã lưu có bài tập con ex_alpha
    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=25,
            user_id=1001,
            exercise_id="ex_alpha",
            submitted_at=deadline_dt,
            is_passed=True,
        )
    )

    # User 1002 đã nộp đủ ex_alpha trước deadline (20:00 VN < 23:59 VN)
    in_memory_submission_repo.add(
        CodingHomeworkSubmission.create_coding(
            homework_id=25,
            user_id=1002,
            exercise_id="ex_alpha",
            submitted_at=datetime(2026, 11, 1, 20, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")),
            is_passed=True,
        )
    )

    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=in_memory_submission_repo,
    )
    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    count = await use_case.execute(target_date=date(2026, 11, 1))

    # User 1002 đã hoàn thành bài ex_alpha nên không bị phạt
    assert count == 0
    assert len(spy_event_bus.published_events) == 0
