from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.homework.application.get_homework_submission_status_use_case import (
    GetHomeworkSubmissionStatusUseCase,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.application.homework_exercise_resolver import (
    HomeworkExerciseResolver,
)
from app.homework.domain.entity import Homework, HomeworkSubmission
from app.homework.domain.value_objects import AssigneeUserInfo
from app.homework.infrastructure.in_memory.in_memory_assignee_repo import (
    InMemoryHomeworkAssigneeRepository,
)
from app.homework.infrastructure.in_memory.in_memory_homework_repo import (
    InMemoryHomeworkRepository,
)
from app.homework.infrastructure.in_memory.in_memory_submission_repo import (
    InMemoryHomeworkSubmissionRepository,
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
async def test_homework_exercise_resolver_priority_and_fallback(
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
):
    """HomeworkExerciseResolver ưu tiên Quiz API và fallback sang DB bài nộp."""
    quiz_api = AsyncMock()

    resolver = HomeworkExerciseResolver(
        quiz_api=quiz_api,
        homework_submission_repo=in_memory_submission_repo,
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
    now = datetime.now(UTC)
    sub1 = HomeworkSubmission.create_coding(
        homework_id=10,
        user_id=1,
        exercise_id="ex-db-1",
        submitted_at=now,
        exercise_title="Bài tập DB 1",
        is_passed=True,
    )
    # Legacy submission với exercise_id dạng sync-legacy-xxx
    sub_legacy = HomeworkSubmission(
        homework_id=10,
        user_id=1,
        submission_type="CODING",
        exercise_id="sync-legacy-123",
        submitted_at=now,
        is_passed=True,
    )

    in_memory_submission_repo.add_submissions([sub1, sub_legacy])

    fallback_exercises = await resolver.get_coding_exercises(
        homework_id=10, slug="lesson-10"
    )
    assert len(fallback_exercises) == 1
    assert fallback_exercises[0].exercise_id == "ex-db-1"
    assert fallback_exercises[0].title == "Bài tập DB 1"


@pytest.mark.asyncio
async def test_get_homework_submission_status_calculates_total_completed_count(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
):
    """Đảm bảo backend tính đúng total_completed_count khi bài yêu cầu cả Coding & Game."""
    class FakeUserRepo:
        pass

    user_repo = FakeUserRepo()

    hw = Homework(
        id=50,
        title="Bài tập Python Full",
        requires_coding=True,
        requires_game=True,
        slug="python-full",
    )
    in_memory_homework_repo.add(hw)

    # Phân công 3 học sinh:
    # - User 1: hoàn thành cả Coding và Game
    # - User 2: chỉ hoàn thành Coding, chưa hoàn thành Game
    # - User 3: chỉ hoàn thành Game, chưa hoàn thành Coding
    in_memory_assignee_repo.set_assignees(
        50,
        [
            AssigneeUserInfo(user_id=1, name="Học sinh 1", deadline=None, avatar_url=None),
            AssigneeUserInfo(user_id=2, name="Học sinh 2", deadline=None, avatar_url=None),
            AssigneeUserInfo(user_id=3, name="Học sinh 3", deadline=None, avatar_url=None),
        ],
    )

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
    in_memory_submission_repo.add_submissions(subs)

    exercise_resolver = AsyncMock(spec=HomeworkExerciseResolver)
    exercise_resolver.get_coding_exercises = AsyncMock(return_value=[])

    use_case = GetHomeworkSubmissionStatusUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        user_repo=user_repo,
        exercise_resolver=exercise_resolver,
    )

    result = await use_case.execute(50)

    assert result is not None
    # Chỉ có User 1 hoàn thành trọn vẹn cả 2 phần yêu cầu
    assert result.total_completed_count == 1
    assert len(result.students) == 3
