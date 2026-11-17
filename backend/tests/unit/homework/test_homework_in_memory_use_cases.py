"""
Unit tests verifying Use Cases running against In-Memory Repositories (Zero-Mock Architecture).
Covers append-only webhook recording, sync exercises catalog (active/inactive/fail-safe),
coding is_passed fidelity, and overdue checking.
"""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.homework.application.backfill_homework_exercises_use_case import (
    BackfillHomeworkExercisesUseCase,
)
from app.homework.application.check_overdue_homework_use_case import (
    CheckOverdueHomeworkUseCase,
)
from app.homework.application.dtos import HomeworkSubmissionWebhookIn
from app.homework.application.get_user_homework_submissions_use_case import (
    GetUserHomeworkSubmissionsUseCase,
)
from app.homework.application.record_submission_use_case import (
    RecordHomeworkSubmissionUseCase,
)
from app.homework.application.sync_homework_use_case import (
    SyncHomeworkFromQuizUseCase,
)
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import SubmissionType
from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    CodingSubmissionDetails,
    GameSubmissionDetails,
    HomeworkOverdueDetected,
)
from tests.fixtures.homework_fixtures import (
    FakeQuizApiClient,
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    SpyEventBus,
    make_exercise,
)


@pytest.mark.asyncio
async def test_record_submission_append_only_and_idempotent(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
):
    """
    - Cùng external_submission_id -> idempotent update (không tạo trùng).
    - Khác external_submission_id dù cùng exercise_id -> append mới, KHÔNG ghi đè mốc submitted_at cũ!
    """
    hw = HomeworkEntity(
        id=1,
        title="Python Basics",
        slug="python-basics",
        requires_coding=True,
        requires_game=False,
    )
    in_memory_homework_repo.create(hw)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
    )

    t1 = datetime(2026, 11, 15, 10, 0, 0, tzinfo=UTC)
    t2 = t1 + timedelta(hours=3)

    # 1. Nộp lần đầu (submission_id="1001", is_passed=False)
    payload1 = HomeworkSubmissionWebhookIn(
        type=SubmissionType.CODING,
        user_id=42,
        lesson_slug="python-basics",
        submission_id="1001",
        exercise_id="ex-func-1",
        exercise_title="Function Exercise 1",
        score=4.0,
        attempt_number=1,
        is_passed=False,
        submitted_at=t1,
        details=CodingSubmissionDetails(submission_id="1001"),
    )
    res1 = await use_case.execute(payload1)
    assert res1.status == "recorded"

    # 2. Gửi lặp cùng submission_id="1001" -> idempotent update
    payload1_retry = payload1.model_copy(update={"is_passed": True, "score": 9.0})
    res1_retry = await use_case.execute(payload1_retry)
    assert res1_retry.status == "updated"
    assert res1_retry.submission_id == res1.submission_id
    assert len(in_memory_submission_repo.get_submissions_by_user(1, 42)) == 1

    # 3. Học viên nộp lần 2 với submission_id="1002" (cùng exercise_id) -> append mới, giữ nguyên t1
    payload2 = HomeworkSubmissionWebhookIn(
        type=SubmissionType.CODING,
        user_id=42,
        lesson_slug="python-basics",
        submission_id="1002",
        exercise_id="ex-func-1",
        exercise_title="Function Exercise 1",
        score=10.0,
        attempt_number=2,
        is_passed=True,
        submitted_at=t2,
        details=CodingSubmissionDetails(submission_id="1002"),
    )
    res2 = await use_case.execute(payload2)
    assert res2.status == "recorded"
    assert res2.submission_id != res1.submission_id

    all_subs = in_memory_submission_repo.get_submissions_by_user(1, 42)
    assert len(all_subs) == 2
    assert {s.submitted_at for s in all_subs} == {t1, t2}


@pytest.mark.asyncio
async def test_record_game_submission_use_case_in_memory(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
):
    hw = HomeworkEntity(
        id=2,
        title="Game Level 1",
        slug="game-level-1",
        requires_coding=False,
        requires_game=True,
    )
    in_memory_homework_repo.add(hw)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
    )

    payload = HomeworkSubmissionWebhookIn(
        type=SubmissionType.GAME,
        user_id=43,
        lesson_slug="game-level-1",
        submission_id="2001",
        score=100.0,
        is_passed=True,
        submitted_at=datetime.now(UTC),
        details=GameSubmissionDetails(gold=50, total_questions=10, correct_count=10),
    )

    res = await use_case.execute(payload)
    assert res.status == "recorded"
    assert res.homework_id == 2

    stored = in_memory_submission_repo.get_submissions_by_user(2, 43)
    assert len(stored) == 1
    assert stored[0].submission_type == SubmissionType.GAME
    assert stored[0].external_submission_id == "2001"
    assert stored[0].score == 100.0


@pytest.mark.asyncio
async def test_sync_homework_updates_exercises_catalog_and_respects_is_passed(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """US3: Sync cập nhật homework_exercises (active/inactive), tôn trọng is_passed=False, cập nhật last_synced_at."""
    in_memory_homework_repo.add(
        HomeworkEntity(
            id=10,
            title="Numpy Lab",
            slug="numpy-lab",
            requires_coding=True,
            requires_game=False,
        )
    )
    in_memory_exercise_repo.sync_exercises(
        10,
        [
            make_exercise(10, "ex-1", "Bài 1 cũ", 1),
            make_exercise(10, "ex-removed", "Bài bị gỡ", 2),
        ],
    )

    fake_quiz_api.set_lesson_metadata(
        "numpy-lab",
        {"has_coding": True, "has_game": False, "coding_count": 2, "game_question_count": 0},
    )
    fake_quiz_api.set_lesson_exercises(
        "numpy-lab",
        [
            {"id": "ex-1", "title": "Bài 1 mới"},
            {"id": "ex-2", "title": "Bài 2 mới"},
        ],
    )
    fake_quiz_api.set_coding_submissions(
        "numpy-lab",
        [
            {
                "submission_id": "quiz-sub-1",
                "user_id": 7,
                "exercise_id": "ex-1",
                "exercise_title": "Bài 1 mới",
                "score": 100.0,
                "status": "PASSED",
                "is_passed": True,
                "submitted_at": "2026-11-10T10:00:00Z",
            },
            {
                "submission_id": "quiz-sub-2",
                "user_id": 7,
                "exercise_id": "ex-2",
                "exercise_title": "Bài 2 mới",
                "score": 20.0,
                "status": "FAILED",
                "is_passed": False,
                "submitted_at": "2026-11-10T11:00:00Z",
            },
        ],
    )

    sync_uc = SyncHomeworkFromQuizUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        quiz_api=fake_quiz_api,  # type: ignore
    )

    res = await sync_uc.execute(10)
    assert res.coding_exercises_count == 2
    assert res.synced_coding_count == 2
    assert res.last_synced_at is not None

    # Kiểm tra danh mục chính thức: ex-removed đã bị deactivate
    active_exs = in_memory_exercise_repo.get_active_by_homework(10)
    assert [e.exercise_id for e in active_exs] == ["ex-1", "ex-2"]
    assert active_exs[0].title == "Bài 1 mới"

    # Kiểm tra tôn trọng is_passed=False cho ex-2
    user_subs = in_memory_submission_repo.get_submissions_by_user(10, 7)
    by_ext_id = {s.external_submission_id: s for s in user_subs}
    assert by_ext_id["quiz-sub-1"].is_passed is True
    assert by_ext_id["quiz-sub-2"].is_passed is False

    # Kiểm tra fail-safe khi Quiz API lỗi mạng: KHÔNG xóa mất danh mục bài con hiện có
    fake_quiz_api.should_fail = True
    await sync_uc.execute(10)
    still_active = in_memory_exercise_repo.get_active_by_homework(10)
    assert [e.exercise_id for e in still_active] == ["ex-1", "ex-2"]


@pytest.mark.asyncio
async def test_backfill_homework_exercises_use_case(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    in_memory_homework_repo.add(HomeworkEntity(id=1, title="Has Slug", slug="ok-slug", requires_coding=True))
    in_memory_homework_repo.add(HomeworkEntity(id=2, title="No Slug", slug=None, link=None, requires_coding=True))
    fake_quiz_api.set_lesson_exercises("ok-slug", [{"id": "ex-ok", "title": "Ex OK"}])

    sync_uc = SyncHomeworkFromQuizUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        quiz_api=fake_quiz_api,  # type: ignore
    )
    backfill_uc = BackfillHomeworkExercisesUseCase(
        homework_repo=in_memory_homework_repo,
        sync_homework_uc=sync_uc,
    )

    res = await backfill_uc.execute(sync_submissions=False)
    assert res.total_homeworks == 2
    assert res.succeeded == 1
    assert res.skipped_no_slug == 1
    assert res.failed == 0
    assert [e.exercise_id for e in in_memory_exercise_repo.get_active_by_homework(1)] == ["ex-ok"]


@pytest.mark.asyncio
async def test_get_user_homework_submissions_use_case_in_memory(
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
):
    use_case = GetUserHomeworkSubmissionsUseCase(
        homework_submission_repo=in_memory_submission_repo
    )
    record_uc = RecordHomeworkSubmissionUseCase(
        homework_repo=InMemoryHomeworkRepository(
            [HomeworkEntity(id=10, title="HW 10", slug="slug-a")]
        ),
        homework_submission_repo=in_memory_submission_repo,
    )
    await record_uc.execute(
        HomeworkSubmissionWebhookIn(
            type=SubmissionType.CODING,
            user_id=1,
            lesson_slug="slug-a",
            exercise_id="ex-1",
            is_passed=True,
            submitted_at=datetime(2026, 11, 14, 10, 0, tzinfo=UTC),
        )
    )
    await record_uc.execute(
        HomeworkSubmissionWebhookIn(
            type=SubmissionType.CODING,
            user_id=2,
            lesson_slug="slug-a",
            exercise_id="ex-1",
            is_passed=False,
            submitted_at=datetime(2026, 11, 14, 11, 0, tzinfo=UTC),
        )
    )

    assert len(await use_case.execute(homework_id=10, user_id=1)) == 1
    assert len(await use_case.execute(homework_id=10, user_id=2)) == 1
    assert len(await use_case.execute(homework_id=10, user_id=3)) == 0


@pytest.mark.asyncio
async def test_check_overdue_homework_use_case_in_memory(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    spy_event_bus: SpyEventBus,
):
    target_deadline_date = date(2026, 11, 10)
    deadline_dt = datetime(2026, 11, 10, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    in_memory_homework_repo.add(
        HomeworkEntity(
            id=99,
            title="Clean Architecture Lab",
            slug="clean-arch-lab",
            requires_coding=True,
            requires_game=False,
        )
    )
    in_memory_exercise_repo.sync_exercises(99, [make_exercise(99, "ex-alpha", "Exercise Alpha", 1)])
    in_memory_assignee_repo.set_homework_info(
        99, title="Clean Architecture Lab", requires_coding=True, requires_game=False, slug="clean-arch-lab"
    )
    in_memory_assignee_repo.set_assignees(
        99,
        [
            AssigneeUserInfo(user_id=10, name="user10", avatar_url=None, deadline=deadline_dt),
            AssigneeUserInfo(user_id=20, name="user20", avatar_url=None, deadline=deadline_dt),
        ],
        default_deadline=deadline_dt,
    )

    record_uc = RecordHomeworkSubmissionUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
    )
    await record_uc.execute(
        HomeworkSubmissionWebhookIn(
            type=SubmissionType.CODING,
            user_id=20,
            lesson_slug="clean-arch-lab",
            exercise_id="ex-alpha",
            is_passed=True,
            submitted_at=datetime(2026, 11, 10, 10, 0, 0, tzinfo=UTC),
        )
    )

    check_uc = CheckOverdueHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        event_bus=spy_event_bus,  # type: ignore
    )

    overdue_count = await check_uc.execute(target_date=target_deadline_date)
    assert overdue_count == 1
    event = spy_event_bus.published_events[0]
    assert isinstance(event, HomeworkOverdueDetected)
    assert event.user_id == 10
    assert "Chưa hoàn thành" in event.reason
