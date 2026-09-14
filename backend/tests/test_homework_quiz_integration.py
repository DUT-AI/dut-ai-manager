"""
Test suite for Homework & Quiz API integration, aggregated per-lesson violation checking,
permission request handling, and rescan use cases.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

try:
    import pytest
except ImportError:
    class DummyPytestMark:
        @staticmethod
        def asyncio(f):
            return f
    class DummyPytest:
        mark = DummyPytestMark()
    pytest = DummyPytest()

from app.homework.domain.entity import Homework
from app.user.domain.entity import UserEntity
from app.homework.application.checker_use_cases import (
    CheckOverdueHomeworkUseCase,
    RescanAllHomeworksUseCase,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.domain.event_bus import EventBus
from app.permission_request.domain.entity import PermissionRequest


@pytest.mark.asyncio
async def test_lesson_aggregated_violation_single_ticket():
    """
    Test Case 1: Học viên thiếu CẢ Coding VÀ Game trong 1 Lesson -> Sinh ĐÚNG 1 VÉ VI PHẠM GỘP.
    Lý do vi phạm phải chứa nội dung tổng hợp cả 'bài tập coding' và 'trắc nghiệm game'.
    """
    print("=" * 60)
    print("Running Test Case 1: Lesson Aggregated Violation (1 Ticket for Coding + Game)")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    lesson_hw = Homework(
        id=101,
        title="Lesson 1: Python Basics & Game Quiz",
        deadline=datetime.now(timezone.utc) - timedelta(hours=2),
        link="https://quiz.dutai.site/lesson/python-lesson-1",
        slug="python-lesson-1",
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {10}
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = []

    # User 10 completed NOTHING on Coding, NOTHING on Game
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
        print(f" -> Ticket for User ID {ev.user_id}: {ev.reason}")

    # Exactly 1 ticket created for User 10
    assert len(published_events) == 1, f"Expected 1 aggregated ticket, got {len(published_events)}"
    reason = published_events[0].reason.lower()
    assert "bài tập coding" in reason and "trắc nghiệm game" in reason
    assert "và không phép" in reason

    print("✅ TEST CASE 1 PASSED SUCCESSFULLY!")
    print("=" * 60)


@pytest.mark.asyncio
async def test_lesson_coding_only_violation():
    """
    Test Case 2: Học viên làm xong Game nhưng THIẾU Coding -> Sinh ĐÚNG 1 VÉ VI PHẠM về Coding.
    """
    print("=" * 60)
    print("Running Test Case 2: Coding Missing Only Violation")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    lesson_hw = Homework(
        id=102,
        title="Lesson 2: Data Structures",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        link="https://quiz.dutai.site/homeworks/ds-lesson-2",
        slug="ds-lesson-2",
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {20}
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = []

    # User 20 completed Game (15/15 questions), but did NOT complete Coding
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[
        {"user_id": 20, "is_completed": True, "total_questions": 15, "answered_questions": 15}
    ])
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

    assert len(published_events) == 1
    reason = published_events[0].reason.lower()
    assert "bài tập coding" in reason
    assert "trắc nghiệm game" not in reason

    print("✅ TEST CASE 2 PASSED SUCCESSFULLY!")
    print("=" * 60)


@pytest.mark.asyncio
async def test_lesson_game_only_violation():
    """
    Test Case 3: Học viên làm xong Coding nhưng THIẾU Game (hoặc làm chưa xong game) -> Sinh 1 VÉ VI PHẠM về Game.
    """
    print("=" * 60)
    print("Running Test Case 3: Game Missing Only Violation")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()

    lesson_hw = Homework(
        id=103,
        title="Lesson 3: Algorithms & Game",
        deadline=datetime.now(timezone.utc) - timedelta(hours=1),
        link="https://quiz.dutai.site/game/algo-game",
        slug="algo-game",
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {30}
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = []

    # User 30 completed Coding, but only answered 3/10 questions in Game
    mock_quiz_api.get_homework_completed_members = AsyncMock(return_value=[{"user_id": 30}])
    mock_quiz_api.get_game_leaderboard = AsyncMock(return_value=[
        {"user_id": 30, "is_completed": True, "total_questions": 10, "answered_questions": 3}
    ])

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

    assert len(published_events) == 1
    reason = published_events[0].reason.lower()
    assert "trắc nghiệm game" in reason

    print("✅ TEST CASE 3 PASSED SUCCESSFULLY!")
    print("=" * 60)


@pytest.mark.asyncio
async def test_valid_postpone_request_skips_entire_lesson():
    """
    Test Case 4: Học viên có đơn xin tạm hoãn hợp lệ -> BỎ QUA HOÀN TOÀN (0 vé vi phạm nào được sinh ra).
    """
    print("=" * 60)
    print("Running Test Case 4: Valid Postpone Request Skips Entire Lesson Check")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)
    now_naive = datetime.now()

    lesson_hw = Homework(
        id=104,
        title="Lesson 4: Permission Test",
        deadline=now - timedelta(hours=5),
        link="https://quiz.dutai.site/homeworks/lesson-4",
        slug="lesson-4",
    )

    # User 40 has valid postpone request until tomorrow
    valid_request = PermissionRequest(
        id=1, user_id=40, created_by=40, homework_id=104,
        start_time=now_naive + timedelta(days=1), category="POSTPONE", note="Bận đột xuất"
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {40}
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = [valid_request]

    # User 40 completed nothing
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

    # 0 tickets because postpone request is valid!
    assert len(published_events) == 0

    print("✅ TEST CASE 4 PASSED SUCCESSFULLY!")
    print("=" * 60)


@pytest.mark.asyncio
async def test_expired_postpone_request_issues_ticket():
    """
    Test Case 5: Học viên có đơn xin tạm hoãn ĐÃ HẾT HẠN -> Phát sinh 1 VÉ VI PHẠM với lý do 'quá thời gian xin hẹn'.
    """
    print("=" * 60)
    print("Running Test Case 5: Expired Postpone Request Issues Ticket")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
    mock_user_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    today = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)
    now_naive = datetime.now()

    lesson_hw = Homework(
        id=105,
        title="Lesson 5: Expired Postpone",
        deadline=now - timedelta(hours=10),
        link="https://quiz.dutai.site/homeworks/lesson-5",
        slug="lesson-5",
    )

    # User 50 has expired postpone request (2 hours ago)
    expired_request = PermissionRequest(
        id=2, user_id=50, created_by=50, homework_id=105,
        start_time=now_naive - timedelta(hours=2), category="POSTPONE", note="Quá hạn hoãn"
    )

    mock_homework_repo.get_by_deadline_date.return_value = [lesson_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = {50}
    mock_permission_repo.get_postpone_requests_for_homeworks.return_value = [expired_request]

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

    assert len(published_events) == 1
    reason = published_events[0].reason.lower()
    assert "quá thời gian xin hẹn" in reason

    print("✅ TEST CASE 5 PASSED SUCCESSFULLY!")
    print("=" * 60)


@pytest.mark.asyncio
async def test_unassigned_legacy_homework_does_not_penalize_users():
    """
    Test Case 6: Bài tập cũ chưa được phân công (assignee_ids và team_ids rỗng)
    -> KHÔNG tự động phạt nhầm toàn bộ active users trong hệ thống.
    """
    print("=" * 60)
    print("Running Test Case 6: Unassigned Legacy Homework Protection")
    print("=" * 60)

    mock_homework_repo = MagicMock()
    mock_permission_repo = MagicMock()
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
        team_ids=[],
    )

    mock_homework_repo.get_by_deadline_date.return_value = [unassigned_hw]
    mock_homework_repo.get_assigned_user_ids.return_value = set()
    mock_user_repo.get_active_users.return_value = [
        UserEntity(id=1, name="Active 1", email="a1@gmail.com"),
        UserEntity(id=2, name="Active 2", email="a2@gmail.com"),
    ]

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

    # Exactly 0 tickets! Active users are NOT penalized for unassigned homework
    assert len(published_events) == 0

    print("✅ TEST CASE 6 PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_lesson_aggregated_violation_single_ticket())
    asyncio.run(test_lesson_coding_only_violation())
    asyncio.run(test_lesson_game_only_violation())
    asyncio.run(test_valid_postpone_request_skips_entire_lesson())
    asyncio.run(test_expired_postpone_request_issues_ticket())
    asyncio.run(test_unassigned_legacy_homework_does_not_penalize_users())

