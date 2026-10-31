"""
Test suite for Homework & Quiz API integration, aggregated per-lesson violation checking,
and rescan use cases.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.homework.application import (
    CheckOverdueHomeworkUseCase,
)
from app.homework.domain.entity import Homework, SubmissionType
from app.homework.domain.value_objects import DueHomeworkAssignment
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import EventBus


@pytest.mark.asyncio
async def test_lesson_aggregated_violation_single_ticket():
    """
    Test Case 1: Học viên thiếu CẢ Coding VÀ Game trong 1 Lesson -> Sinh ĐÚNG 1 VÉ VI PHẠM GỘP.
    Lý do vi phạm phải chứa nội dung tổng hợp cả 'bài tập coding' và 'trắc nghiệm game'.
    """
    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()

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

    # User 10 completed NOTHING on Coding, NOTHING on Game in DB
    mock_submission_repo.get_submissions_by_homework.return_value = []
    mock_submission_repo.has_valid_submission.return_value = False

    mock_quiz_api = MagicMock(spec=QuizApiClient)
    mock_quiz_api.get_lesson_exercises = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        quiz_api=mock_quiz_api,
    )

    published_events = []

    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, "publish", side_effect=mock_publish):
        await use_case.execute(target_date=today)

    # Exactly 1 ticket created for User 10
    assert len(published_events) == 1, (
        f"Expected 1 aggregated ticket, got {len(published_events)}"
    )
    reason = published_events[0].reason.lower()
    assert "bài tập coding" in reason and "trắc nghiệm game" in reason


@pytest.mark.asyncio
async def test_lesson_coding_only_violation():
    """
    Test Case 2: Học viên làm xong Game nhưng THIẾU Coding -> Sinh ĐÚNG 1 VÉ VI PHẠM về Coding.
    """
    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()

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

    # User 20 completed Game in DB, but did NOT complete Coding
    mock_submission_repo.get_submissions_by_homework.return_value = []

    def mock_has_valid(homework_id, user_id, submission_type, deadline):
        return submission_type == SubmissionType.GAME

    mock_submission_repo.has_valid_submission.side_effect = mock_has_valid

    mock_quiz_api = MagicMock(spec=QuizApiClient)
    mock_quiz_api.get_lesson_exercises = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        quiz_api=mock_quiz_api,
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
    """
    Test Case 3: Học viên làm xong Coding nhưng THIẾU Game (hoặc làm chưa xong game) -> Sinh 1 VÉ VI PHẠM về Game.
    """
    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()

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

    # User 30 completed Coding, but did NOT complete Game
    mock_submission_repo.get_submissions_by_homework.return_value = []

    def mock_has_valid(homework_id, user_id, submission_type, deadline):
        return submission_type == SubmissionType.CODING

    mock_submission_repo.has_valid_submission.side_effect = mock_has_valid

    mock_quiz_api = MagicMock(spec=QuizApiClient)
    mock_quiz_api.get_lesson_exercises = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        quiz_api=mock_quiz_api,
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
    """
    Test Case 4: Bài tập cũ chưa được phân công (assignee_ids rỗng)
    -> KHÔNG tự động phạt nhầm toàn bộ active users trong hệ thống.
    """
    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()

    today = datetime.now(UTC).date()

    mock_assignee_repo = MagicMock()
    mock_assignee_repo.get_by_deadline_date.return_value = []

    mock_quiz_api = MagicMock(spec=QuizApiClient)
    mock_quiz_api.get_lesson_exercises = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        homework_assignee_repo=mock_assignee_repo,
        quiz_api=mock_quiz_api,
    )

    published_events = []

    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, "publish", side_effect=mock_publish):
        await use_case.execute(target_date=today)

    # Exactly 0 tickets! Active users are NOT penalized for unassigned homework
    assert len(published_events) == 0


@pytest.mark.asyncio
async def test_sync_homework_from_quiz_with_string_timestamps():
    """
    Test Case 5: Đồng bộ bài tập từ Quiz API khi Quiz trả về submitted_at/completed_at dạng chuỗi ISO.
    """
    from app.homework.application.sync_homework_use_case import (
        SyncHomeworkFromQuizUseCase,
    )

    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
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
    mock_submission_repo.find_submission_match.return_value = None

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
        homework_submission_repo=mock_submission_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=201)

    assert result["synced_coding_count"] == 1
    assert result["synced_game_count"] == 1
    assert mock_submission_repo.add_submission.call_count == 2
