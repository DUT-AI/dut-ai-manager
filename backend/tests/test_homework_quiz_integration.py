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

from app.homework.domain.entity import Homework, HomeworkSubmission
from app.homework.domain.value_objects import HomeworkStatus
from app.shared.domain.value_objects import UserRef
from app.homework.application.use_cases import CheckOverdueHomeworkUseCase
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import EventBus


async def test_quiz_api_integration():
    print("=" * 60)
    print("Running Test Case 1: Quiz API Integration & Homework Coding Check")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    dummy_homework = Homework(
        id=1,
        title="Bài tập YOLOv3",
        description="",
        deadline=datetime.now(timezone.utc) - timedelta(hours=2),
        link="https://quiz.dutai.site/homeworks/yolov3",
        homework_slug="yolov3",
        game_slug=None,
        submissions=[]
    )

    sub10 = HomeworkSubmission(
        id=100,
        homework_id=1,
        owner_id=10,
        status=HomeworkStatus.NOT_SUBMITTED,
        owner=UserRef(id=10, name="User 10", email="user10@gmail.com")
    )
    sub11 = HomeworkSubmission(
        id=101,
        homework_id=1,
        owner_id=11,
        status=HomeworkStatus.NOT_SUBMITTED,
        owner=UserRef(id=11, name="User 11", email="user11@gmail.com")
    )
    dummy_homework.submissions = [sub10, sub11]

    mock_homework_repo.get_by_deadline_date.return_value = [dummy_homework]
    mock_submission_repo.get_by_homework_id.return_value = [sub10, sub11]
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = []

    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[{"user_id": 10}])
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        submission_repo=mock_submission_repo,
        permission_repo=mock_permission_repo,
        quiz_api=mock_quiz_api,
    )

    published_events = []
    async def mock_publish(event):
        published_events.append(event)

    with patch.object(EventBus, 'publish', side_effect=mock_publish):
        await use_case.execute(target_date=today)

    print(f"Total Overdue Events Published: {len(published_events)}")
    for ev in published_events:
        print(f" -> Event for User ID {ev.user_id}: {ev.reason}")

    assert len(published_events) == 1
    assert published_events[0].user_id == 11
    assert "chưa làm bài tập coding" in published_events[0].reason.lower()

    print("✅ TEST CASE 1 PASSED SUCCESSFULLY!")
    print("=" * 60)


async def test_separate_game_and_coding_violations():
    print("=" * 60)
    print("Running Test Case 2: Separate Game & Coding Tickets + Full Game Check")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    # Homework with BOTH game_slug AND homework_slug
    dummy_homework = Homework(
        id=2,
        title="Bài tập Python & Quiz Game",
        description="",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        link="https://quiz.dutai.site/game/python-quiz",
        homework_slug="python-coding",
        game_slug="python-quiz",
        submissions=[]
    )

    sub20 = HomeworkSubmission(
        id=200,
        homework_id=2,
        owner_id=20,
        status=HomeworkStatus.NOT_SUBMITTED,
        owner=UserRef(id=20, name="User 20", email="user20@gmail.com")
    )
    dummy_homework.submissions = [sub20]

    mock_homework_repo.get_by_deadline_date.return_value = [dummy_homework]
    mock_submission_repo.get_by_homework_id.return_value = [sub20]
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = []

    # User 20 played only 2 of 15 questions in the game (NOT full game!)
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[
        {"user_id": 20, "email": "user20@gmail.com", "is_completed": True, "total_questions": 15, "answered_questions": 2}
    ])
    # User 20 also did NOT complete coding
    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        submission_repo=mock_submission_repo,
        permission_repo=mock_permission_repo,
        quiz_api=mock_quiz_api,
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
    assert any("chưa làm game" in r.lower() for r in reasons)
    assert any("chưa làm bài tập coding" in r.lower() for r in reasons)

    print("✅ TEST CASE 2 PASSED SUCCESSFULLY!")
    print("=" * 60)


async def test_with_valid_and_expired_permission_requests():
    print("=" * 60)
    print("Running Test Case 3: Permission Requests (Valid vs Expired)")
    print("=" * 60)

    from app.permission_request.domain.entity import PermissionRequest
    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)
    now_naive = datetime.now()

    dummy_homework = Homework(
        id=3,
        title="Bài tập Permission",
        description="",
        deadline=now - timedelta(hours=24), # Hết hạn hôm qua
        link="",
        homework_slug="perm-coding",
        game_slug=None,
        submissions=[]
    )

    # User 30: Valid permission request (until tomorrow)
    sub30 = HomeworkSubmission(
        id=300,
        homework_id=3,
        owner_id=30,
        status=HomeworkStatus.NOT_SUBMITTED,
        owner=UserRef(id=30, name="User 30", email="u30@gmail.com")
    )
    # User 31: Expired permission request (expired 2 hours ago)
    sub31 = HomeworkSubmission(
        id=301,
        homework_id=3,
        owner_id=31,
        status=HomeworkStatus.NOT_SUBMITTED,
        owner=UserRef(id=31, name="User 31", email="u31@gmail.com")
    )
    dummy_homework.submissions = [sub30, sub31]

    mock_homework_repo.get_by_deadline_date.return_value = [dummy_homework]
    mock_submission_repo.get_by_homework_id.return_value = [sub30, sub31]
    
    req_30 = PermissionRequest(
        id=1, user_id=30, homework_id=3, start_time=now_naive + timedelta(days=1), category="POSTPONE", note="Test"
    )
    req_31 = PermissionRequest(
        id=2, user_id=31, homework_id=3, start_time=now_naive - timedelta(hours=2), category="POSTPONE", note="Test"
    )
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = [req_30, req_31]

    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[])

    use_case = CheckOverdueHomeworkUseCase(
        homework_repo=mock_homework_repo,
        submission_repo=mock_submission_repo,
        permission_repo=mock_permission_repo,
        quiz_api=mock_quiz_api,
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
    # User 31 has expired permission -> 1 ticket with "quá thời gian xin hẹn"
    assert len(published_events) == 1
    assert published_events[0].user_id == 31
    assert "quá thời gian xin hẹn" in published_events[0].reason.lower()

    print("✅ TEST CASE 3 PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_quiz_api_integration())
    asyncio.run(test_separate_game_and_coding_violations())
    asyncio.run(test_with_valid_and_expired_permission_requests())
