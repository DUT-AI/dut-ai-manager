from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.homework.application.dtos import (
    CategorySubmissionStatus,
    HomeworkSubmissionStatusResponse,
    UserSubmissionInfo,
)
from app.homework.application.get_homework_submission_status_use_case import (
    GetHomeworkSubmissionStatusUseCase,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.application.homework_exercise_resolver import (
    HomeworkExerciseResolver,
)
from app.homework.domain.entity import Homework, HomeworkSubmission
from app.homework.infrastructure.homework_assignee_repository import (
    AssigneeUserInfo,
)


def test_homework_extract_slug_and_effective_slug():
    """Entity Homework là SSOT chịu trách nhiệm trích xuất slug hiệu lực."""
    # 1. Có slug trực tiếp
    hw1 = Homework(title="HW 1", slug="  bai-hoc-1  ", link="https://quiz.ai/lessons/bai-hoc-cu")
    assert hw1.effective_slug == "bai-hoc-1"
    assert Homework.extract_slug(hw1.link, hw1.slug) == "bai-hoc-1"

    # 2. Không có slug, trích xuất từ link
    hw2 = Homework(title="HW 2", slug="", link="https://example.com/homeworks/bai-tap-oop?tab=1#top")
    assert hw2.effective_slug == "bai-tap-oop"

    hw3 = Homework(title="HW 3", link="https://quiz.example.com/game/quiz-01/")
    assert hw3.effective_slug == "quiz-01"

    # 3. QuizSubmissionHelper ủy quyền chính xác cho HomeworkEntity
    assert QuizSubmissionHelper.extract_slug_from_entity(hw2) == "bai-tap-oop"
    assert QuizSubmissionHelper.extract_slug(hw1.link, hw1.slug) == "bai-hoc-1"


@pytest.mark.asyncio
async def test_homework_exercise_resolver_priority_and_fallback():
    """HomeworkExerciseResolver ưu tiên Quiz API và fallback sang DB bài nộp."""
    quiz_api = MagicMock()
    submission_repo = MagicMock()

    resolver = HomeworkExerciseResolver(
        quiz_api=quiz_api,
        homework_submission_repo=submission_repo,
    )

    # 1. Thành công từ Quiz API
    quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[
            {"id": "ex-1", "title": "Bài tập 1"},
            {"id": "ex-2", "title": "Bài tập 2"},
        ]
    )
    exercises = await resolver.get_coding_exercises(homework_id=10, slug="lesson-10")
    assert len(exercises) == 2
    assert exercises[0].exercise_id == "ex-1"
    assert exercises[1].exercise_id == "ex-2"

    req_ids = await resolver.resolve_required_exercise_ids(10, "lesson-10")
    assert req_ids == {"ex-1", "ex-2"}

    # 2. Fallback sang DB khi Quiz API thất bại hoặc slug không có
    quiz_api.get_lesson_exercises = AsyncMock(side_effect=Exception("API Down"))
    sub1 = MagicMock(spec=HomeworkSubmission)
    sub1.submission_type = "CODING"
    sub1.exercise_id = "ex-db-1"
    sub1.exercise_title = "Bài tập DB 1"

    sub_legacy = MagicMock(spec=HomeworkSubmission)
    sub_legacy.submission_type = "CODING"
    sub_legacy.exercise_id = "sync-legacy-123"

    submission_repo.get_submissions_by_homework.return_value = [sub1, sub_legacy]

    fallback_exercises = await resolver.get_coding_exercises(
        homework_id=10, slug="lesson-10"
    )
    assert len(fallback_exercises) == 1
    assert fallback_exercises[0].exercise_id == "ex-db-1"
    assert fallback_exercises[0].title == "Bài tập DB 1"


@pytest.mark.asyncio
async def test_get_homework_submission_status_calculates_total_completed_count():
    """Đảm bảo backend tính đúng total_completed_count khi bài yêu cầu cả Coding & Game."""
    homework_repo = MagicMock()
    submission_repo = MagicMock()
    assignee_repo = MagicMock()
    user_repo = MagicMock()
    exercise_resolver = MagicMock(spec=HomeworkExerciseResolver)

    hw = Homework(
        id=50,
        title="Bài tập Python Full",
        requires_coding=True,
        requires_game=True,
        slug="python-full",
    )
    homework_repo.get_by_id.return_value = hw

    # Phân công 3 học sinh:
    # - User 1: hoàn thành cả Coding và Game
    # - User 2: chỉ hoàn thành Coding, chưa hoàn thành Game
    # - User 3: chỉ hoàn thành Game, chưa hoàn thành Coding
    assignees = [
        AssigneeUserInfo(user_id=1, name="Học sinh 1", deadline=None, avatar_url=None),
        AssigneeUserInfo(user_id=2, name="Học sinh 2", deadline=None, avatar_url=None),
        AssigneeUserInfo(user_id=3, name="Học sinh 3", deadline=None, avatar_url=None),
    ]
    assignee_repo.get_assignees_with_user_info.return_value = assignees

    # Submissions
    now = datetime.now(UTC)
    subs = [
        # User 1
        HomeworkSubmission(
            homework_id=50,
            user_id=1,
            submission_type="CODING",
            is_passed=True,
            exercise_id="ex-1",
            submitted_at=now,
        ),
        HomeworkSubmission(
            homework_id=50,
            user_id=1,
            submission_type="GAME",
            is_passed=True,
            submitted_at=now,
        ),
        # User 2
        HomeworkSubmission(
            homework_id=50,
            user_id=2,
            submission_type="CODING",
            is_passed=True,
            exercise_id="ex-1",
            submitted_at=now,
        ),
        # User 3
        HomeworkSubmission(
            homework_id=50,
            user_id=3,
            submission_type="GAME",
            is_passed=True,
            submitted_at=now,
        ),
    ]
    submission_repo.get_submissions_by_homework.return_value = subs

    exercise_resolver.get_coding_exercises = AsyncMock(return_value=[])

    use_case = GetHomeworkSubmissionStatusUseCase(
        homework_repo=homework_repo,
        homework_submission_repo=submission_repo,
        homework_assignee_repo=assignee_repo,
        user_repo=user_repo,
        exercise_resolver=exercise_resolver,
    )

    result = await use_case.execute(50)

    assert result is not None
    # Chỉ có User 1 hoàn thành trọn vẹn cả 2 phần yêu cầu
    assert result.total_completed_count == 1
    assert len(result.students) == 3
