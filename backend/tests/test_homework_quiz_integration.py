"""
Test suite for Homework & Quiz API integration and overdue checking logic.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from app.homework.domain.entity import Homework
from app.user.domain.entity import UserEntity
from app.homework.application.use_cases import CheckOverdueHomeworkUseCase
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import EventBus


async def test_quiz_api_integration():
    print("=" * 60)
    print("Running Test Case 1: Quiz API Integration & Homework Coding Check")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    dummy_homework = Homework(
        id=1,
        title="Bài tập YOLOv3",
        description="",
        deadline=datetime.now(timezone.utc) - timedelta(hours=2),
        link="https://quiz.dutai.site/homeworks/yolov3",
        slug="yolov3",
    )

    user10 = UserEntity(id=10, name="User 10", email="user10@gmail.com")
    user11 = UserEntity(id=11, name="User 11", email="user11@gmail.com")

    mock_homework_repo.get_by_deadline_date.return_value = [dummy_homework]
    mock_homework_repo.get_assigned_user_ids.return_value = {10, 11}
    mock_user_repo.get_by_id.side_effect = lambda uid: user10 if uid == 10 else user11
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = []

    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[{"user_id": 10}])
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        permission_repo=mock_permission_repo,
        quiz_api=mock_quiz_api,
        user_repo=mock_user_repo,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
        await use_case.execute(target_date=today)

    print(f"Total Overdue Events Published: {len(published_events)}")
    for ev in published_events:
        print(f" -> Event for User ID {ev.user_id}: {ev.reason}")

    assert len(published_events) == 3  # User 10 missed game; User 11 missed coding + game
    assert any(ev.user_id == 11 and "code" in ev.reason.lower() for ev in published_events)
    assert any(ev.user_id == 10 and "game" in ev.reason.lower() for ev in published_events)

    print("✅ TEST CASE 1 PASSED SUCCESSFULLY!")
    print("=" * 60)


async def test_separate_game_and_coding_violations():
    print("=" * 60)
    print("Running Test Case 2: Separate Game & Coding Tickets + Full Game Check")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    dummy_homework = Homework(
        id=2,
        title="Bài tập Python & Quiz Game",
        description="",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        link="https://quiz.dutai.site/game/python-quiz",
        slug="python-quiz",
    )

    user20 = UserEntity(id=20, name="User 20", email="user20@gmail.com")

    mock_homework_repo.get_by_deadline_date.return_value = [dummy_homework]
    mock_homework_repo.get_assigned_user_ids.return_value = {20}
    mock_user_repo.get_by_id.return_value = user20
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = []

    # User 20 played only 2 of 15 questions in the game (NOT full game!)
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[
        {"user_id": 20, "email": "user20@gmail.com", "is_completed": True, "total_questions": 15, "answered_questions": 2}
    ])
    # User 20 also did NOT complete coding
    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        permission_repo=mock_permission_repo,
        quiz_api=mock_quiz_api,
        user_repo=mock_user_repo,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
        await use_case.execute(target_date=today)

    print(f"Total Overdue Events Published: {len(published_events)}")
    for ev in published_events:
        print(f" -> Event for User ID {ev.user_id}: {ev.reason}")

    # User 20 failed BOTH Game (only 2/15) AND Coding -> 2 SEPARATE violation tickets created!
    assert len(published_events) == 2, f"Expected 2 separate violation tickets, got {len(published_events)}"
    reasons = [e.reason for e in published_events]
    assert any("game" in r.lower() for r in reasons)
    assert any("code" in r.lower() for r in reasons)

    print("✅ TEST CASE 2 PASSED SUCCESSFULLY!")
    print("=" * 60)


async def test_with_valid_and_expired_permission_requests():
    print("=" * 60)
    print("Running Test Case 3: Permission Requests (Valid vs Expired)")
    print("=" * 60)

    from app.permission_request.domain.entity import PermissionRequest
    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)
    now_naive = datetime.now()

    dummy_homework = Homework(
        id=3,
        title="Bài tập Permission",
        description="",
        deadline=now - timedelta(hours=24),
        link="",
        slug="perm-coding",
    )

    user30 = UserEntity(id=30, name="User 30", email="u30@gmail.com")
    user31 = UserEntity(id=31, name="User 31", email="u31@gmail.com")

    mock_homework_repo.get_by_deadline_date.return_value = [dummy_homework]
    mock_homework_repo.get_assigned_user_ids.return_value = {30, 31}
    mock_user_repo.get_by_id.side_effect = lambda uid: user30 if uid == 30 else user31
    
    req_30 = PermissionRequest(
        id=1, user_id=30, created_by=30, homework_id=3, start_time=now_naive + timedelta(days=1), category="POSTPONE", note="Test"
    )
    req_31 = PermissionRequest(
        id=2, user_id=31, created_by=31, homework_id=3, start_time=now_naive - timedelta(hours=2), category="POSTPONE", note="Test"
    )
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = [req_30, req_31]

    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[])
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        permission_repo=mock_permission_repo,
        quiz_api=mock_quiz_api,
        user_repo=mock_user_repo,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
        await use_case.execute(target_date=today)

    print(f"Total Overdue Events Published: {len(published_events)}")
    for ev in published_events:
        print(f" -> Event for User ID {ev.user_id}: {ev.reason}")

    # User 30 has valid permission -> No ticket. 
    # User 31 has expired permission -> 2 tickets (coding + game) with "quá thời gian xin hẹn"
    assert len(published_events) == 2
    assert all(ev.user_id == 31 for ev in published_events)
    assert all("quá thời gian xin hẹn" in ev.reason.lower() for ev in published_events)

    print("✅ TEST CASE 3 PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_quiz_api_integration())
    asyncio.run(test_separate_game_and_coding_violations())
    asyncio.run(test_with_valid_and_expired_permission_requests())
