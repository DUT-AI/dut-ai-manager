"""
Test suite for Homework & Quiz API integration, aggregated per-lesson violation checking,
and rescan use cases.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.homework.domain.entity import Homework
from app.user.domain.entity import UserEntity
from app.homework.application import (
    CheckOverdueHomeworkUseCase,
    RescanAllHomeworksUseCase,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import EventBus


@pytest.mark.asyncio
async def test_lesson_aggregated_violation_single_ticket():
    """
    Test Case 1: Học viên thiếu CẢ Coding VÀ Game trong 1 Lesson -> Sinh ĐÚNG 1 VÉ VI PHẠM GỘP.
    Lý do vi phạm phải chứa nội dung tổng hợp cả 'bài tập coding' và 'trắc nghiệm game'.
    """
    mock_homework_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    lesson_hw = Homework(
        id=101,
        title="Lesson 1: Python Basics & Game Quiz",
        deadline=datetime.now(timezone.utc) - timedelta(hours=2),
        link="https://quiz.dutai.site/lesson/python-lesson-1",
        slug="python-lesson-1",
        assignee_ids=[10],
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {10}

    # User 10 completed NOTHING on Coding, NOTHING on Game
    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[])
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        quiz_api=mock_quiz_api,
        user_repo=mock_user_repo,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
        await use_case.execute(target_date=today)

    # Exactly 1 ticket created for User 10
    assert len(published_events) == 1, f"Expected 1 aggregated ticket, got {len(published_events)}"
    reason = published_events[0].reason.lower()
    assert "bài tập coding" in reason and "trắc nghiệm game" in reason


@pytest.mark.asyncio
async def test_lesson_coding_only_violation():
    """
    Test Case 2: Học viên làm xong Game nhưng THIẾU Coding -> Sinh ĐÚNG 1 VÉ VI PHẠM về Coding.
    """
    mock_homework_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    lesson_hw = Homework(
        id=102,
        title="Lesson 2: Data Structures",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        link="https://quiz.dutai.site/homeworks/ds-lesson-2",
        slug="ds-lesson-2",
        assignee_ids=[20],
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {20}

    # User 20 completed Game (15/15 questions), but did NOT complete Coding
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[
        {"user_id": 20, "is_completed": True, "total_questions": 15, "answered_questions": 15}
    ])
    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        quiz_api=mock_quiz_api,
        user_repo=mock_user_repo,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
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
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    lesson_hw = Homework(
        id=103,
        title="Lesson 3: Algorithms & Game",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        link="https://quiz.dutai.site/game/algo-game",
        slug="algo-game",
        assignee_ids=[30],
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {30}

    # User 30 completed Coding, but only answered 3/10 questions in Game
    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[{"user_id": 30}])
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[
        {"user_id": 30, "is_completed": True, "total_questions": 10, "answered_questions": 3}
    ])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        quiz_api=mock_quiz_api,
        user_repo=mock_user_repo,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
        await use_case.execute(target_date=today)

    assert len(published_events) == 1
    reason = published_events[0].reason.lower()
    assert "trắc nghiệm game" in reason


@pytest.mark.asyncio
async def test_unassigned_legacy_homework_does_not_penalize_users():
    """
    Test Case 4: Bài tập cũ chưa được phân công (assignee_ids rỗng)
    -> KHÔNG tự động phạt nhầm toàn bộ active users trong hệ thống.
    """
    mock_homework_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    unassigned_hw = Homework(
        id=106,
        title="Unassigned Legacy Homework",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        link="https://quiz.dutai.site/homeworks/unassigned",
        slug="unassigned",
        assignee_ids=[],
    )

    mock_homework_repo.get_by_deadline_date.return_value = [unassigned_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = set()
    mock_user_repo.get_active_users.return_value = [
        UserEntity(id=1, name="Active 1", email="a1@gmail.com"),
        UserEntity(id=2, name="Active 2", email="a2@gmail.com"),
    ]

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        quiz_api=mock_quiz_api,
        user_repo=mock_user_repo,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
        await use_case.execute(target_date=today)

    # Exactly 0 tickets! Active users are NOT penalized for unassigned homework
    assert len(published_events) == 0
