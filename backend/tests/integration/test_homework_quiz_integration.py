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
        homework_submission_repo=mock_submission_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=201)

    assert result["synced_coding_count"] == 1
    assert result["synced_game_count"] == 1
    assert mock_submission_repo.add_submission.call_count == 2


@pytest.mark.asyncio
async def test_sync_homework_refreshes_metadata_flags_and_syncs_both():
    """
    Test Case 6 (US1 & US2): Tự động làm mới cấu hình bài tập từ Quiz API khi đồng bộ.
    Ban đầu requires_coding=False, requires_game=False.
    Quiz API trả về metadata has_coding=True, has_game=True, coding_count=2, game_question_count=10.
    Sau đồng bộ: Homework entity được update requires_coding=True, requires_game=True và cả Coding + Game đều được kéo.
    """
    from app.homework.application.sync_homework_use_case import (
        SyncHomeworkFromQuizUseCase,
    )

    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
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
    mock_submission_repo.find_submission_match.return_value = None

    # Quiz metadata & exercises
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

    # Submissions
    mock_quiz_api.get_homework_submissions_for_sync = AsyncMock(
        return_value=[
            {
                "submission_id": "sub-c1",
                "user_id": 15,
                "exercise_id": "ex-1",
                "exercise_title": "Linear Regression",
                "score": 100,
                "attempt_number": 1,
                "submitted_at": "2026-11-01T08:00:00Z",
            }
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
        homework_submission_repo=mock_submission_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=301)

    # 1. Kiểm tra homework entity được update cờ và lưu vào repo
    assert hw.requires_coding is True
    assert hw.requires_game is True
    mock_homework_repo.save.assert_called_once()

    # 2. Kiểm tra cả Coding và Game đều được sync thành công
    assert result["requires_coding"] is True
    assert result["requires_game"] is True
    assert result["coding_exercises_count"] == 2
    assert result["game_questions_count"] == 10
    assert result["synced_coding_count"] == 1
    assert result["synced_game_count"] == 1
    assert mock_submission_repo.add_submission.call_count == 2


@pytest.mark.asyncio
async def test_sync_homework_metadata_failsafe_on_network_error():
    """
    Test Case 7 (US1 Fail-Safe): Khi Quiz API metadata lỗi mạng hoặc gián đoạn,
    tiến trình đồng bộ không crash và fallback tiếp tục đồng bộ bài nộp bình thường.
    """
    from app.homework.application.sync_homework_use_case import (
        SyncHomeworkFromQuizUseCase,
    )

    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
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
    mock_submission_repo.find_submission_match.return_value = None

    # Giả lập Quiz API lỗi mạng khi lấy metadata & exercises
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
        homework_submission_repo=mock_submission_repo,
        quiz_api=mock_quiz_api,
    )

    # Không raise exception (Fail-Safe), tiếp tục sync coding theo cờ hiện tại
    result = await use_case.execute(homework_id=302)

    assert result["requires_coding"] is True
    assert result["requires_game"] is False
    assert result["synced_coding_count"] == 1
    assert mock_submission_repo.add_submission.call_count == 1


@pytest.mark.asyncio
async def test_sync_homework_detects_new_exercises_when_no_submissions():
    """
    Test Case 8 (US2): Giảng viên thêm bài tập con mới nhưng chưa ai nộp.
    Đồng bộ vẫn nhận diện được chính xác số lượng bài tập con mới trên Quiz.
    """
    from app.homework.application.sync_homework_use_case import (
        SyncHomeworkFromQuizUseCase,
    )

    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    hw = Homework(
        id=303,
        title="Computer Vision",
        link="https://quiz.dutai.site/lesson/computer-vision",
        slug="computer-vision",
        requires_coding=True,
        requires_game=False,
    )
    mock_homework_repo.get_by_id.return_value = hw

    # Quiz có 3 bài tập con mới thêm
    mock_quiz_api.get_lesson_metadata = AsyncMock(
        return_value={
            "slug": "computer-vision",
            "name": "Computer Vision",
            "has_coding": True,
            "has_game": False,
            "coding_count": 3,
            "game_question_count": 0,
        }
    )
    mock_quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[
            {"id": "cv-1", "title": "Image Filtering"},
            {"id": "cv-2", "title": "Edge Detection"},
            {"id": "cv-3", "title": "Corner Detection"},
        ]
    )

    # Chưa có học sinh nào nộp bài
    mock_quiz_api.get_homework_submissions_for_sync = AsyncMock(return_value=[])

    use_case = SyncHomeworkFromQuizUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=303)

    assert result["coding_exercises_count"] == 3
    assert result["game_questions_count"] == 0
    assert result["synced_coding_count"] == 0
    assert result["updated_coding_count"] == 0


@pytest.mark.asyncio
async def test_sync_homework_result_payload_contract():
    """
    Test Case 9 (US3): Kiểm tra kết quả trả về của use case tuân thủ cấu trúc SyncHomeworkResult.
    """
    from app.homework.application.sync_homework_use_case import (
        SyncHomeworkFromQuizUseCase,
    )

    mock_homework_repo = MagicMock()
    mock_submission_repo = MagicMock()
    mock_quiz_api = MagicMock(spec=QuizApiClient)

    hw = Homework(
        id=304,
        title="NLP Transformer",
        link="https://quiz.dutai.site/lesson/transformer",
        slug="transformer",
        requires_coding=True,
        requires_game=True,
    )
    mock_homework_repo.get_by_id.return_value = hw
    mock_submission_repo.find_submission_match.return_value = None

    mock_quiz_api.get_lesson_metadata = AsyncMock(
        return_value={
            "has_coding": True,
            "has_game": True,
            "coding_count": 1,
            "game_question_count": 5,
        }
    )
    mock_quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[{"id": "tf-1", "title": "Self Attention"}]
    )
    mock_quiz_api.get_homework_submissions_for_sync = AsyncMock(return_value=[])
    mock_quiz_api.get_game_sessions_for_sync = AsyncMock(return_value=[])

    use_case = SyncHomeworkFromQuizUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
        quiz_api=mock_quiz_api,
    )

    result = await use_case.execute(homework_id=304)

    expected_keys = {
        "homework_id",
        "title",
        "requires_coding",
        "requires_game",
        "coding_exercises_count",
        "game_questions_count",
        "synced_coding_count",
        "updated_coding_count",
        "synced_game_count",
        "updated_game_count",
        "message",
    }
    assert expected_keys.issubset(set(result.keys()))
    assert isinstance(result["message"], str)
    assert len(result["message"]) > 0

