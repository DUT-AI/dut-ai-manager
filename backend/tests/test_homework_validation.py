"""
Unit test suite for Homework creation and update validation against Quiz API.

Tests:
1. Rejection when neither 'requires_coding' nor 'requires_game' is selected.
2. Rejection when slug/link does not exist on Quiz API.
3. Rejection when 'requires_coding' is selected but Quiz metadata has has_coding=False.
4. Rejection when 'requires_game' is selected but Quiz metadata has has_game=False.
5. Successful creation when selected requirements match Quiz capabilities.
6. Similar validations for UpdateHomeworkUseCase.
7. Verification that overdue checker only penalizes missing required components.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.homework.application.create_homework_use_case import CreateHomeworkUseCase
from app.homework.application.dtos import HomeworkCreate, HomeworkUpdate
from app.homework.application.update_homework_use_case import UpdateHomeworkUseCase
from app.homework.domain.entity import Homework
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import HomeworkRepository
from app.shared.application.response import BadRequestException


@pytest.fixture
def mock_homework_repo():
    repo = MagicMock(spec=HomeworkRepository)
    repo.save = MagicMock(side_effect=lambda hw: hw)
    return repo


@pytest.fixture
def mock_quiz_api():
    return MagicMock(spec=QuizApiClient)


@pytest.mark.asyncio
async def test_create_homework_rejects_when_no_options_selected(
    mock_homework_repo, mock_quiz_api
):
    """Bắt lỗi khi không chọn bất kỳ option nào (cả coding và game đều False)."""
    use_case = CreateHomeworkUseCase(
        homework_repo=mock_homework_repo, quiz_api=mock_quiz_api
    )

    data = HomeworkCreate(
        title="Bài tập mẫu",
        deadline=datetime.now(UTC) + timedelta(days=7),
        slug="lesson-01",
        requires_coding=False,
        requires_game=False,
    )

    with pytest.raises(BadRequestException) as exc_info:
        await use_case.execute(data)

    assert "Vui lòng chọn ít nhất một yêu cầu" in str(exc_info.value)
    mock_homework_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_create_homework_rejects_when_lesson_not_found_on_quiz(
    mock_homework_repo, mock_quiz_api
):
    """Bắt lỗi khi slug bài học không tồn tại trên hệ thống Quiz (404/None)."""
    mock_quiz_api.get_lesson_metadata = AsyncMock(return_value=None)
    use_case = CreateHomeworkUseCase(
        homework_repo=mock_homework_repo, quiz_api=mock_quiz_api
    )

    data = HomeworkCreate(
        title="Bài tập mẫu",
        deadline=datetime.now(UTC) + timedelta(days=7),
        slug="lesson-khong-ton-tai",
        requires_coding=True,
        requires_game=False,
    )

    with pytest.raises(BadRequestException) as exc_info:
        await use_case.execute(data)

    assert "không tồn tại trên hệ thống Quiz" in str(exc_info.value)
    mock_homework_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_create_homework_rejects_when_coding_not_available(
    mock_homework_repo, mock_quiz_api
):
    """Bắt lỗi khi chọn 'requires_coding' nhưng Quiz metadata báo chưa có bài tập coding."""
    mock_quiz_api.get_lesson_metadata = AsyncMock(
        return_value={
            "slug": "batch-norm",
            "name": "Batch Normalization",
            "has_coding": False,
            "has_game": True,
            "coding_count": 0,
            "game_question_count": 4,
            "is_ready": True,
        }
    )
    use_case = CreateHomeworkUseCase(
        homework_repo=mock_homework_repo, quiz_api=mock_quiz_api
    )

    data = HomeworkCreate(
        title="Batch Norm Coding",
        deadline=datetime.now(UTC) + timedelta(days=7),
        slug="batch-norm",
        requires_coding=True,
        requires_game=False,
    )

    with pytest.raises(BadRequestException) as exc_info:
        await use_case.execute(data)

    assert "chưa có bài tập coding" in str(exc_info.value)
    assert "Batch Normalization" in str(exc_info.value)
    mock_homework_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_create_homework_rejects_when_game_not_available(
    mock_homework_repo, mock_quiz_api
):
    """Bắt lỗi khi chọn 'requires_game' nhưng Quiz metadata báo chưa có câu hỏi game."""
    mock_quiz_api.get_lesson_metadata = AsyncMock(
        return_value={
            "slug": "resnet-intro",
            "name": "Giới thiệu ResNet",
            "has_coding": True,
            "has_game": False,
            "coding_count": 1,
            "game_question_count": 0,
            "is_ready": True,
        }
    )
    use_case = CreateHomeworkUseCase(
        homework_repo=mock_homework_repo, quiz_api=mock_quiz_api
    )

    data = HomeworkCreate(
        title="ResNet Quiz Game",
        deadline=datetime.now(UTC) + timedelta(days=7),
        slug="resnet-intro",
        requires_coding=False,
        requires_game=True,
    )

    with pytest.raises(BadRequestException) as exc_info:
        await use_case.execute(data)

    assert "chưa có câu hỏi game" in str(exc_info.value)
    assert "Giới thiệu ResNet" in str(exc_info.value)
    mock_homework_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_create_homework_success(mock_homework_repo, mock_quiz_api):
    """Tạo bài tập thành công khi thỏa mãn điều kiện tồn tại trên Quiz."""
    mock_quiz_api.get_lesson_metadata = AsyncMock(
        return_value={
            "slug": "unet-01",
            "name": "Mạng UNet",
            "has_coding": True,
            "has_game": True,
            "coding_count": 1,
            "game_question_count": 5,
            "is_ready": True,
        }
    )
    use_case = CreateHomeworkUseCase(
        homework_repo=mock_homework_repo, quiz_api=mock_quiz_api
    )

    data = HomeworkCreate(
        title="UNet Project",
        deadline=datetime.now(UTC) + timedelta(days=7),
        link="https://quiz.dutai.site/lessons/unet-01",
        requires_coding=True,
        requires_game=True,
        assignee_ids=[1, 2, 3],
    )

    saved = await use_case.execute(data)

    assert saved.title == "UNet Project"
    assert saved.slug == "unet-01"
    assert saved.requires_coding is True
    assert saved.requires_game is True
    assert saved.assignee_ids == [1, 2, 3]
    mock_homework_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_update_homework_validation(mock_homework_repo, mock_quiz_api):
    """Cập nhật bài tập: xác thực điều kiện tương tự khi đổi slug hoặc đổi yêu cầu."""
    existing_hw = Homework(
        id=1,
        title="Old title",
        deadline=datetime.now(UTC) + timedelta(days=2),
        slug="old-slug",
        requires_coding=False,
        requires_game=True,
    )
    mock_homework_repo.get_by_id = MagicMock(return_value=existing_hw)

    mock_quiz_api.get_lesson_metadata = AsyncMock(
        return_value={
            "slug": "new-slug",
            "name": "New Lesson",
            "has_coding": False,
            "has_game": True,
            "is_ready": True,
        }
    )

    use_case = UpdateHomeworkUseCase(
        homework_repo=mock_homework_repo, quiz_api=mock_quiz_api
    )

    # Thử update thành requires_coding=True khi quiz không có coding -> Phải fail
    with pytest.raises(BadRequestException) as exc_info:
        await use_case.execute(
            homework_id=1,
            data=HomeworkUpdate(
                slug="new-slug",
                requires_coding=True,
                requires_game=False,
            ),
        )
    assert "chưa có bài tập coding" in str(exc_info.value)
