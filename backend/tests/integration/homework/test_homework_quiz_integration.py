"""
Test suite for Homework & Quiz API integration, aggregated per-lesson violation checking,
and sync use cases with official homework_exercises catalog.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.homework.application import (
    CheckOverdueHomeworkUseCase,
    SyncHomeworkFromQuizUseCase,
)
from app.homework.application.dtos import SyncHomeworkResult
from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    GameHomeworkSubmission,
    Homework,
)
from app.homework.domain.value_objects import DueHomeworkAssignment
from app.homework.infrastructure.in_memory import (
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import EventBus


@pytest.mark.asyncio
async def test_lesson_aggregated_violation_single_ticket():
    """Học viên thiếu CẢ Coding VÀ Game -> Sinh ĐÚNG 1 VÉ VI PHẠM GỘP."""
    mock_homework_repo = MagicMock()
    mock_homework_repo.get_by_id.return_value = None
    mock_submission_repo = MagicMock()
    exercise_repo = InMemoryHomeworkExerciseRepository()

    today = datetime.now(UTC).date()
    dl = datetime.now(UTC) - timedelta(hours=2)

    mock_assignee_repo = MagicMock()
    mock_assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=101,
            user_id=10,
            homework_title="Lesson 1: Python Basics & Game Quiz",
            deadline=dl,
            requires_coding=True,
            requires_game=True,
        )
    ]
    mock_submission_repo.get_submissions_by_user.return_value = []

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        homework_exercise_repo=exercise_repo,
    )

    published_events = []

    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, "publish", side_effect=mock_publish):
        await use_case.execute(target_date=today)

    assert len(published_events) == 1
    reason = published_events[0].reason.lower()
    assert "bài tập coding" in reason and "trắc nghiệm game" in reason


@pytest.mark.asyncio
async def test_lesson_coding_only_violation():
    """Học viên xong Game nhưng thiếu Coding -> Sinh ĐÚNG 1 vé về Coding."""
    mock_homework_repo = MagicMock()
    mock_homework_repo.get_by_id.return_value = None
    mock_submission_repo = MagicMock()
    exercise_repo = InMemoryHomeworkExerciseRepository()

    today = datetime.now(UTC).date()
    dl = datetime.now(UTC) - timedelta(hours=1)

    mock_assignee_repo = MagicMock()
    mock_assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=102,
            user_id=20,
            homework_title="Lesson 2: Data Structures",
            deadline=dl,
            requires_coding=True,
            requires_game=True,
        )
    ]
    mock_submission_repo.get_submissions_by_user.return_value = [
        GameHomeworkSubmission.create_game(
            homework_id=102,
            user_id=20,
            submitted_at=dl - timedelta(minutes=10),
            is_passed=True,
        )
    ]

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        homework_exercise_repo=exercise_repo,
    )

    published_events = []

    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, "publish", side_effect=mock_publish):
        await use_case.execute(target_date=today)

    assert len(published_events) == 1
    reason = published_events[0].reason.lower()
    assert "bài tập coding" in reason
    assert "trắc nghiệm game" not in reason


@pytest.mark.asyncio
async def test_lesson_game_only_violation():
    """Học viên xong Coding nhưng thiếu Game -> Sinh ĐÚNG 1 vé về Game."""
    mock_homework_repo = MagicMock()
    mock_homework_repo.get_by_id.return_value = None
    mock_submission_repo = MagicMock()
    exercise_repo = InMemoryHomeworkExerciseRepository()

    today = datetime.now(UTC).date()
    dl = datetime.now(UTC) - timedelta(hours=1)

    mock_assignee_repo = MagicMock()
    mock_assignee_repo.get_by_deadline_date.return_value = [
        DueHomeworkAssignment(
            homework_id=103,
            user_id=30,
            homework_title="Lesson 3: Algorithms & Game",
            deadline=dl,
            requires_coding=True,
            requires_game=True,
        )
    ]
    mock_submission_repo.get_submissions_by_user.return_value = [
        CodingHomeworkSubmission.create_coding(
            homework_id=103,
            user_id=30,
            exercise_id="default",
            submitted_at=dl - timedelta(minutes=10),
            is_passed=True,
        )
    ]

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        homework_exercise_repo=exercise_repo,
    )

    published_events = []

    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, "publish", side_effect=mock_publish):
        await use_case.execute(target_date=today)

    assert len(published_events) == 1
    reason = published_events[0].reason.lower()
    assert "trắc nghiệm game" in reason
    assert "bài tập coding" not in reason


@pytest.mark.asyncio
async def test_unassigned_legacy_homework_does_not_penalize_users():
    """Bài tập chưa có assignee -> không phạt nhầm active users."""
    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
    mock_assignee_repo = MagicMock()
    mock_assignee_repo.get_by_deadline_date.return_value = []
    exercise_repo = InMemoryHomeworkExerciseRepository()

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        homework_exercise_repo=exercise_repo,
    )

    published_events = []

    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, "publish", side_effect=mock_publish):
        await use_case.execute(target_date=datetime.now(UTC).date())

    assert len(published_events) == 0


@pytest.mark.asyncio
async def test_sync_homework_from_quiz_with_string_timestamps():
    """Đồng bộ bài tập từ Quiz API khi Quiz trả về submitted_at/completed_at dạng chuỗi ISO."""
    mock_homework_repo = MagicMock()
    submission_repo = InMemoryHomeworkSubmissionRepository()
    exercise_repo = InMemoryHomeworkExerciseRepository()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    hw = Homework(
        id=201,
        title="Representation Learning",
        link="https://quiz.dutai.site/lesson/representation-learning",
        slug="representation-learning",
        requires_coding=True,
        requires_game=True,
    )
    mock_homework_repo.get_by_id.return_value = hw
    mock_quiz_api.get_lesson_metadata = AsyncMock(return_value=None)
    mock_quiz_api.get_lesson_exercises = AsyncMock(return_value=None)
    mock_quiz_api.get_homework_submissions_for_sync = AsyncMock(
        return_value=[
            {
                "submission_id": "sub-1",
                "user_id": 10,
                "exercise_id": "ex-1",
                "exercise_title": "Exercise 1",
                "score": 100,
                "attempt_number": 1,
                "submitted_at": "2026-10-06T11:20:00Z",
            }
        ]
    )
    mock_quiz_api.get_game_sessions_for_sync = AsyncMock(
        return_value=[
            {
                "session_id": "sess-1",
                "user_id": 10,
                "is_completed": True,
                "completed_at": "2026-10-06T11:25:00.000Z",
                "final_score": 150,
            }
        ]
    )

    use_case = SyncHomeworkFromQuizUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=submission_repo,
        homework_exercise_repo=exercise_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=201)

    assert isinstance(result, SyncHomeworkResult)
    assert result.synced_coding_count == 1
    assert result.synced_game_count == 1
    assert result.last_synced_at is not None
    assert submission_repo.count() == 2


@pytest.mark.asyncio
async def test_sync_homework_refreshes_metadata_flags_exercises_and_respects_failed_coding():
    """Sync tự làm mới cờ requires_coding/requires_game, danh mục bài con và tôn trọng status=FAILED."""
    mock_homework_repo = MagicMock()
    submission_repo = InMemoryHomeworkSubmissionRepository()
    exercise_repo = InMemoryHomeworkExerciseRepository()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    hw = Homework(
        id=301,
        title="Machine Learning 101",
        link="https://quiz.dutai.site/lesson/ml-101",
        slug="ml-101",
        requires_coding=False,
        requires_game=False,
    )
    mock_homework_repo.get_by_id.return_value = hw
    mock_quiz_api.get_lesson_metadata = AsyncMock(
        return_value={
            "slug": "ml-101",
            "name": "Machine Learning 101",
            "has_coding": True,
            "has_game": True,
            "coding_count": 2,
            "game_question_count": 10,
        }
    )
    mock_quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[
            {"id": "ex-1", "title": "Linear Regression"},
            {"id": "ex-2", "title": "Logistic Regression"},
        ]
    )
    mock_quiz_api.get_homework_submissions_for_sync = AsyncMock(
        return_value=[
            {
                "submission_id": "sub-c1",
                "user_id": 15,
                "exercise_id": "ex-1",
                "exercise_title": "Linear Regression",
                "score": 100,
                "status": "PASSED",
                "attempt_number": 1,
                "submitted_at": "2026-11-01T08:00:00Z",
            },
            {
                "submission_id": "sub-c2",
                "user_id": 15,
                "exercise_id": "ex-2",
                "exercise_title": "Logistic Regression",
                "score": 0,
                "status": "FAILED",
                "attempt_number": 1,
                "submitted_at": "2026-11-01T08:15:00Z",
            },
        ]
    )
    mock_quiz_api.get_game_sessions_for_sync = AsyncMock(
        return_value=[
            {
                "session_id": "sess-g1",
                "user_id": 15,
                "is_completed": True,
                "completed_at": "2026-11-01T08:30:00Z",
                "final_score": 100,
            }
        ]
    )

    use_case = SyncHomeworkFromQuizUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=submission_repo,
        homework_exercise_repo=exercise_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=301)

    assert hw.requires_coding is True
    assert hw.requires_game is True
    assert result.coding_exercises_count == 2
    assert result.game_questions_count == 10
    assert result.synced_coding_count == 2
    assert result.synced_game_count == 1
    assert [e.exercise_id for e in exercise_repo.get_active_by_homework(301)] == ["ex-1", "ex-2"]

    subs = {s.external_submission_id: s for s in submission_repo.get_submissions_by_user(301, 15)}
    assert subs["sub-c1"].is_passed is True
    assert subs["sub-c2"].is_passed is False


@pytest.mark.asyncio
async def test_sync_homework_metadata_failsafe_on_network_error():
    """Khi Quiz API lỗi mạng ở metadata/exercises, giữ nguyên danh mục cũ và tiếp tục đồng bộ submissions."""
    mock_homework_repo = MagicMock()
    submission_repo = InMemoryHomeworkSubmissionRepository()
    exercise_repo = InMemoryHomeworkExerciseRepository()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    hw = Homework(
        id=302,
        title="Deep Learning",
        link="https://quiz.dutai.site/lesson/deep-learning",
        slug="deep-learning",
        requires_coding=True,
        requires_game=False,
    )
    mock_homework_repo.get_by_id.return_value = hw
    mock_quiz_api.get_lesson_metadata = AsyncMock(
        side_effect=RuntimeError("Cannot connect to Quiz metadata service")
    )
    mock_quiz_api.get_lesson_exercises = AsyncMock(
        side_effect=RuntimeError("Cannot connect to Quiz exercises service")
    )
    mock_quiz_api.get_homework_submissions_for_sync = AsyncMock(
        return_value=[
            {
                "submission_id": "sub-dl-1",
                "user_id": 22,
                "exercise_id": "ex-dl-1",
                "exercise_title": "Backpropagation",
                "score": 95,
                "attempt_number": 1,
                "submitted_at": "2026-11-01T09:00:00Z",
            }
        ]
    )

    use_case = SyncHomeworkFromQuizUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=submission_repo,
        homework_exercise_repo=exercise_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=302)

    assert result.requires_coding is True
    assert result.requires_game is False
    assert result.synced_coding_count == 1
    assert submission_repo.count() == 1
