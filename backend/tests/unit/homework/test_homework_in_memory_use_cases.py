"""
Unit tests verifying Use Cases running against In-Memory Repositories (Zero-Mock Architecture).
Ensures that business flows execute completely on RAM state without touching database or using mock objects.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.homework.application.check_overdue_homework_use_case import (
    CheckOverdueHomeworkUseCase,
)
from app.homework.application.dtos import (
    HomeworkSubmissionWebhookIn,
)
from app.homework.application.get_user_homework_submissions_use_case import (
    GetUserHomeworkSubmissionsUseCase,
)
from app.homework.application.homework_exercise_resolver import (
    HomeworkExerciseResolver,
)
from app.homework.application.record_submission_use_case import (
    RecordHomeworkSubmissionUseCase,
)
from app.homework.domain.entity import (
    Homework as HomeworkEntity,
)
from app.homework.domain.entity import (
    SubmissionType,
)
from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    CodingSubmissionDetails,
    GameSubmissionDetails,
    HomeworkOverdueDetected,
)
from app.homework.infrastructure.in_memory import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
)
from app.shared.domain.event_bus import DomainEvent


class FakeQuizApiClient:
    """Fake QuizApiClient returning static exercise metadata for tests."""

    def __init__(self, exercises: list[dict] | None = None):
        self._exercises = exercises or []

    async def get_lesson_exercises(self, slug: str) -> list[dict]:
        return self._exercises


class SpyEventBus:
    """In-memory event bus spy for capturing published domain events."""

    def __init__(self):
        self.published_events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published_events.append(event)


@pytest.fixture
def homework_repo() -> InMemoryHomeworkRepository:
    return InMemoryHomeworkRepository()


@pytest.fixture
def submission_repo() -> InMemoryHomeworkSubmissionRepository:
    return InMemoryHomeworkSubmissionRepository()


@pytest.fixture
def assignee_repo() -> InMemoryHomeworkAssigneeRepository:
    return InMemoryHomeworkAssigneeRepository()


@pytest.fixture
def spy_event_bus() -> SpyEventBus:
    return SpyEventBus()


@pytest.mark.asyncio
async def test_record_submission_use_case_in_memory(
    homework_repo: InMemoryHomeworkRepository,
    submission_repo: InMemoryHomeworkSubmissionRepository,
):
    """
    Kịch bản: Webhook gửi bài nộp Coding mới, sau đó gửi bài nộp cập nhật.
    Xác minh: Lưu và cập nhật thành công trên RAM không cần database hay mock.
    """
    # 1. Seed homework
    hw = HomeworkEntity(
        id=1,
        title="Python Basics",
        slug="python-basics",
        requires_coding=True,
        requires_game=False,
    )
    homework_repo.create(hw)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
    )

    submitted_at = datetime(2026, 11, 15, 10, 0, 0, tzinfo=UTC)

    # 2. Gửi webhook nộp bài lần đầu (Failed)
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
        submitted_at=submitted_at,
        details=CodingSubmissionDetails(code="def foo(): pass", test_cases_passed=2),
    )

    res1 = await use_case.execute(payload1)
    assert res1.status == "recorded"
    assert res1.homework_id == 1
    assert res1.user_id == 42
    assert res1.exercise_id == "ex-func-1"

    # Kiểm tra repository state
    stored_subs = submission_repo.get_submissions_by_user(1, 42)
    assert len(stored_subs) == 1
    assert stored_subs[0].is_passed is False
    assert stored_subs[0].score == 4.0

    # 3. Gửi webhook cập nhật bài nộp lần 2 (Passed - Idempotent Upsert)
    payload2 = HomeworkSubmissionWebhookIn(
        type=SubmissionType.CODING,
        user_id=42,
        lesson_slug="python-basics",
        submission_id="1001",
        exercise_id="ex-func-1",
        exercise_title="Function Exercise 1",
        score=10.0,
        attempt_number=2,
        is_passed=True,
        submitted_at=submitted_at,
        details=CodingSubmissionDetails(code="def foo(): return 1", test_cases_passed=5),
    )

    res2 = await use_case.execute(payload2)
    assert res2.status == "updated"
    assert res2.submission_id == res1.submission_id

    # Đảm bảo vẫn chỉ có 1 bản ghi nộp bài duy nhất được cập nhật
    updated_subs = submission_repo.get_submissions_by_user(1, 42)
    assert len(updated_subs) == 1
    assert updated_subs[0].is_passed is True
    assert updated_subs[0].score == 10.0
    assert updated_subs[0].attempt_number == 2


@pytest.mark.asyncio
async def test_record_game_submission_use_case_in_memory(
    homework_repo: InMemoryHomeworkRepository,
    submission_repo: InMemoryHomeworkSubmissionRepository,
):
    """
    Kịch bản: Webhook gửi bài nộp Game.
    Xác minh: Lưu thành công GameSubmissionDetails vào RAM.
    """
    hw = HomeworkEntity(
        id=2,
        title="Game Level 1",
        slug="game-level-1",
        requires_coding=False,
        requires_game=True,
    )
    homework_repo.add(hw)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
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

    stored = submission_repo.get_submissions_by_user(2, 43)
    assert len(stored) == 1
    assert stored[0].submission_type == SubmissionType.GAME
    assert stored[0].score == 100.0
    assert stored[0].details.gold == 50


@pytest.mark.asyncio
async def test_get_user_homework_submissions_use_case_in_memory(
    homework_repo: InMemoryHomeworkRepository,
    submission_repo: InMemoryHomeworkSubmissionRepository,
):
    """
    Kịch bản: Lấy danh sách lịch sử nộp bài của một học viên cụ thể.
    Xác minh: Trả về chính xác các bản ghi của user đó, không bị lẫn user khác.
    """
    use_case = GetUserHomeworkSubmissionsUseCase(homework_submission_repo=submission_repo)

    # Nộp cho user 1
    sub1_payload = HomeworkSubmissionWebhookIn(
        type=SubmissionType.CODING,
        user_id=1,
        lesson_slug="slug-a",
        exercise_id="ex-1",
        is_passed=True,
        submitted_at=datetime(2026, 11, 14, 10, 0, tzinfo=UTC),
    )
    # Nộp cho user 2
    sub2_payload = HomeworkSubmissionWebhookIn(
        type=SubmissionType.CODING,
        user_id=2,
        lesson_slug="slug-a",
        exercise_id="ex-1",
        is_passed=False,
        submitted_at=datetime(2026, 11, 14, 11, 0, tzinfo=UTC),
    )

    record_uc = RecordHomeworkSubmissionUseCase(
        homework_repo=InMemoryHomeworkRepository([
            HomeworkEntity(id=10, title="HW 10", slug="slug-a")
        ]),
        homework_submission_repo=submission_repo,
    )
    await record_uc.execute(sub1_payload)
    await record_uc.execute(sub2_payload)

    # Truy vấn lịch sử user 1
    user1_history = await use_case.execute(homework_id=10, user_id=1)
    assert len(user1_history) == 1
    assert user1_history[0].user_id == 1
    assert user1_history[0].is_passed is True

    # Truy vấn lịch sử user 2
    user2_history = await use_case.execute(homework_id=10, user_id=2)
    assert len(user2_history) == 1
    assert user2_history[0].user_id == 2
    assert user2_history[0].is_passed is False

    # Truy vấn user 3 (chưa nộp)
    user3_history = await use_case.execute(homework_id=10, user_id=3)
    assert len(user3_history) == 0


@pytest.mark.asyncio
async def test_check_overdue_homework_use_case_in_memory(
    homework_repo: InMemoryHomeworkRepository,
    submission_repo: InMemoryHomeworkSubmissionRepository,
    assignee_repo: InMemoryHomeworkAssigneeRepository,
    spy_event_bus: SpyEventBus,
):
    """
    Kịch bản: Kiểm tra quá hạn bài tập:
    - User 10: Chưa nộp -> Phát hiện vi phạm và bắn sự kiện qua EventBus.
    - User 20: Đã nộp đủ bài trước deadline -> Không bị vi phạm.
    """
    target_deadline_date = date(2026, 11, 10)
    deadline_dt = datetime(2026, 11, 10, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

    # 1. Tạo bài tập yêu cầu coding với 1 bài tập con "ex-alpha"
    hw = HomeworkEntity(
        id=99,
        title="Clean Architecture Lab",
        slug="clean-arch-lab",
        requires_coding=True,
        requires_game=False,
    )
    homework_repo.add(hw)

    # 2. Phân công cho User 10 và User 20 cùng deadline
    assignee_repo.set_homework_info(
        99,
        title="Clean Architecture Lab",
        requires_coding=True,
        requires_game=False,
        slug="clean-arch-lab",
    )
    assignee_repo.set_assignees(
        99,
        [
            AssigneeUserInfo(user_id=10, name="user10", avatar_url=None, deadline=deadline_dt),
            AssigneeUserInfo(user_id=20, name="user20", avatar_url=None, deadline=deadline_dt),
        ],
        default_deadline=deadline_dt,
    )

    # 3. User 20 nộp bài hợp lệ trước deadline (10:00 UTC = 17:00 VN < 23:59 VN)
    record_uc = RecordHomeworkSubmissionUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
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

    # 4. Fake Quiz API chứa bài tập con "ex-alpha"
    fake_quiz_api = FakeQuizApiClient(
        exercises=[{"id": "ex-alpha", "title": "Exercise Alpha"}]
    )
    exercise_resolver = HomeworkExerciseResolver(
        quiz_api=fake_quiz_api,  # type: ignore
        homework_submission_repo=submission_repo,
    )

    # 5. Khởi tạo Use Case với In-Memory Repositories và Spy Event Bus
    check_uc = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        exercise_resolver=exercise_resolver,
        event_bus=spy_event_bus,  # type: ignore
    )

    # 6. Thực thi quét hạn
    overdue_count = await check_uc.execute(target_date=target_deadline_date)

    # 7. Xác minh kết quả
    assert overdue_count == 1
    assert len(spy_event_bus.published_events) == 1

    event = spy_event_bus.published_events[0]
    assert isinstance(event, HomeworkOverdueDetected)
    assert event.user_id == 10  # Chỉ user 10 bị quá hạn
    assert event.homework_id == 99
    assert "Chưa hoàn thành" in event.reason
