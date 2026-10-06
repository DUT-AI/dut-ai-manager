from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.homework.application import CheckOverdueHomeworkUseCase
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.value_objects import HomeworkOverdueDetected


@pytest.mark.asyncio
async def test_check_overdue_homework_publishes_event():
    homework_repo = MagicMock()
    quiz_api = MagicMock()
    user_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    # Create dummy homework due today with assignee user 101 and 102
    hw = HomeworkEntity(
        id=1,
        title="Bài tập Python OOP",
        slug="python-oop",
        deadline=datetime(2026, 9, 25, 23, 59),
        link="https://quiz.example.com/homeworks/python-oop",
        assignee_ids=[101, 102],
    )
    homework_repo.get_by_deadline_date.return_value = [hw]

    # User 101 submitted coding, User 102 has NOT submitted; No game component for this homework (returns None)
    quiz_api.get_homework_completed_members = AsyncMock(
        return_value=[{"user_id": 101, "submission_count": 1}]
    )
    quiz_api.get_lesson_exercises = AsyncMock(return_value=[])
    quiz_api.get_game_leaderboard = AsyncMock(return_value=None)

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        quiz_api=quiz_api,
        user_repo=user_repo,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 9, 25))

    # User 102 should trigger HomeworkOverdueDetected event
    assert count >= 1
    assert event_bus.publish.called

    published_events = [call[0][0] for call in event_bus.publish.call_args_list]
    overdue_events = [
        e for e in published_events if isinstance(e, HomeworkOverdueDetected)
    ]
    assert len(overdue_events) >= 1
    assert overdue_events[0].user_id == 102
    assert overdue_events[0].homework_id == 1


@pytest.mark.asyncio
async def test_check_overdue_multi_exercise_partial_submission_flags_overdue():
    """Học viên chỉ nộp 1/2 bài tập con sẽ bị tính là quá hạn bài tập coding."""
    homework_repo = MagicMock()
    quiz_api = MagicMock()
    user_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    hw = HomeworkEntity(
        id=2,
        title="Lesson 2: Multitask",
        slug="lesson-2-multi",
        deadline=datetime(2026, 10, 1, 23, 59),
        link="https://quiz.example.com/homeworks/lesson-2-multi",
        assignee_ids=[201],
    )
    homework_repo.get_by_deadline_date.return_value = [hw]

    # Lesson có 2 bài tập con: ex-1 và ex-2
    quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[
            {"id": "ex-1", "title": "Ex 1"},
            {"id": "ex-2", "title": "Ex 2"},
        ]
    )
    # Quiz completed members rỗng (chưa hoàn thành 100% trên Quiz)
    quiz_api.get_homework_completed_members = AsyncMock(return_value=[])
    quiz_api.get_game_leaderboard = AsyncMock(return_value=None)

    # Trong DB Manager, user 201 chỉ nộp ex-1
    homework_repo.get_submitted_exercise_ids.return_value = {"ex-1"}

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        quiz_api=quiz_api,
        user_repo=user_repo,
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
    quiz_api = MagicMock()
    user_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    hw = HomeworkEntity(
        id=3,
        title="Lesson 3: Multitask Complete",
        slug="lesson-3-multi",
        deadline=datetime(2026, 10, 1, 23, 59),
        link="https://quiz.example.com/homeworks/lesson-3-multi",
        assignee_ids=[301],
    )
    homework_repo.get_by_deadline_date.return_value = [hw]

    # Lesson có 2 bài tập con: ex-1 và ex-2
    quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[
            {"id": "ex-1", "title": "Ex 1"},
            {"id": "ex-2", "title": "Ex 2"},
        ]
    )
    quiz_api.get_homework_completed_members = AsyncMock(return_value=[])
    quiz_api.get_game_leaderboard = AsyncMock(return_value=None)

    # Trong DB Manager, user 301 đã nộp cả ex-1 và ex-2
    homework_repo.get_submitted_exercise_ids.return_value = {"ex-1", "ex-2"}

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        quiz_api=quiz_api,
        user_repo=user_repo,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 10, 1))

    assert count == 0
    assert not event_bus.publish.called

