from unittest.mock import AsyncMock, MagicMock

import pytest

from app.homework.application.get_homework_detail_use_case import (
    GetHomeworkDetailUseCase,
)
from app.homework.domain.entity import Homework


@pytest.mark.asyncio
async def test_get_homework_detail_returns_coding_exercises_from_quiz_api():
    homework_repo = MagicMock()
    homework_assignee_repo = MagicMock()
    quiz_api = MagicMock()
    homework_submission_repo = MagicMock()

    mock_hw = Homework(
        id=79,
        title="Gen2: Đại số tuyến tính",
        slug="dai-so-tuyen-tinh",
        requires_coding=True,
        requires_game=True,
    )
    homework_repo.get_by_id.return_value = mock_hw
    homework_assignee_repo.get_assignees_with_user_info.return_value = []

    quiz_api.get_lesson_exercises = AsyncMock(
        return_value=[
            {"id": "ex-1", "title": "Bài tập 1"},
            {"id": "ex-2", "title": "Bài tập 2"},
        ]
    )

    use_case = GetHomeworkDetailUseCase(
        homework_repo=homework_repo,
        homework_assignee_repo=homework_assignee_repo,
        quiz_api=quiz_api,
        homework_submission_repo=homework_submission_repo,
    )

    result = await use_case.execute(79)

    assert result is not None
    assert result.id == 79
    assert len(result.coding_exercises) == 2
    assert result.coding_exercises[0].exercise_id == "ex-1"
    assert result.coding_exercises[0].title == "Bài tập 1"
    assert result.coding_exercises[1].exercise_id == "ex-2"


@pytest.mark.asyncio
async def test_get_homework_detail_fallback_to_submissions_when_quiz_api_fails():
    homework_repo = MagicMock()
    homework_assignee_repo = MagicMock()
    quiz_api = MagicMock()
    homework_submission_repo = MagicMock()

    mock_hw = Homework(
        id=79,
        title="Gen2: Đại số tuyến tính",
        slug="dai-so-tuyen-tinh",
        requires_coding=True,
        requires_game=True,
    )
    homework_repo.get_by_id.return_value = mock_hw
    homework_assignee_repo.get_assignees_with_user_info.return_value = []

    quiz_api.get_lesson_exercises = AsyncMock(side_effect=Exception("API Error"))

    sub1 = MagicMock()
    sub1.submission_type = "CODING"
    sub1.exercise_id = "ex-a"
    sub1.exercise_title = "Bài tập A"

    sub2 = MagicMock()
    sub2.submission_type = "GAME"
    sub2.exercise_id = None

    homework_submission_repo.get_submissions_by_homework.return_value = [sub1, sub2]

    use_case = GetHomeworkDetailUseCase(
        homework_repo=homework_repo,
        homework_assignee_repo=homework_assignee_repo,
        quiz_api=quiz_api,
        homework_submission_repo=homework_submission_repo,
    )

    result = await use_case.execute(79)

    assert result is not None
    assert len(result.coding_exercises) == 1
    assert result.coding_exercises[0].exercise_id == "ex-a"
    assert result.coding_exercises[0].title == "Bài tập A"
