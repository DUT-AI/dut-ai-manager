import asyncio
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.homework.application.checker_use_cases import CheckOverdueHomeworkUseCase
from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.value_objects import HomeworkOverdueDetected


@pytest.mark.asyncio
async def test_check_overdue_homework_publishes_event():
    homework_repo = MagicMock()
    quiz_api = MagicMock()
    user_repo = MagicMock()
    team_repo = MagicMock()
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

    # User 101 submitted coding, User 102 has NOT submitted
    quiz_api.get_homework_completed_members = AsyncMock(return_value=[{"user_id": 101, "submission_count": 1}])
    quiz_api.get_game_leaderboard = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=homework_repo,
        quiz_api=quiz_api,
        user_repo=user_repo,
        team_repo=team_repo,
        event_bus=event_bus,
    )

    count = await use_case.execute(target_date=date(2026, 9, 25))

    # User 102 should trigger HomeworkOverdueDetected event
    assert count >= 1
    assert event_bus.publish.called

    published_events = [call[0][0] for call in event_bus.publish.call_args_list]
    overdue_events = [e for e in published_events if isinstance(e, HomeworkOverdueDetected)]
    assert len(overdue_events) >= 1
    assert overdue_events[0].user_id == 102
    assert overdue_events[0].homework_id == 1
