"""
Unit test suite for Homework creation and update validation against Quiz API.
Uses In-Memory Fake Repositories (Zero-Mock for persistence layer).
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.homework.application.create_homework_use_case import CreateHomeworkUseCase
from app.homework.application.dtos import HomeworkCreate, HomeworkUpdate
from app.homework.application.update_homework_use_case import UpdateHomeworkUseCase
from app.homework.domain.entity import Homework, HomeworkSubmission, SubmissionType
from app.shared.application.response import BadRequestException
from tests.fixtures.homework_fixtures import (
    FakeQuizApiClient,
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkRepository,
)


@pytest.mark.asyncio
async def test_create_homework_rejects_when_no_options_selected(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Bắt lỗi khi không chọn bất kỳ option nào (cả coding và game đều False)."""
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
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
    assert in_memory_homework_repo.get_all() == []


@pytest.mark.asyncio
async def test_create_homework_rejects_when_lesson_not_found_on_quiz(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Bắt lỗi khi slug bài học không tồn tại trên hệ thống Quiz (404/None)."""
    fake_quiz_api.set_lesson_metadata("lesson-khong-ton-tai", None)  # type: ignore
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
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
    assert in_memory_homework_repo.get_all() == []


@pytest.mark.asyncio
async def test_create_homework_rejects_when_coding_not_available(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Bắt lỗi khi chọn 'requires_coding' nhưng Quiz metadata báo chưa có bài tập coding."""
    fake_quiz_api.set_lesson_metadata(
        "batch-norm",
        {
            "slug": "batch-norm",
            "name": "Batch Normalization",
            "has_coding": False,
            "has_game": True,
            "coding_count": 0,
            "game_question_count": 4,
            "is_ready": True,
        },
    )
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
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
    assert in_memory_homework_repo.get_all() == []


@pytest.mark.asyncio
async def test_create_homework_rejects_when_game_not_available(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Bắt lỗi khi chọn 'requires_game' nhưng Quiz metadata báo chưa có câu hỏi game."""
    fake_quiz_api.set_lesson_metadata(
        "resnet-intro",
        {
            "slug": "resnet-intro",
            "name": "Giới thiệu ResNet",
            "has_coding": True,
            "has_game": False,
            "coding_count": 1,
            "game_question_count": 0,
            "is_ready": True,
        },
    )
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
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
    assert in_memory_homework_repo.get_all() == []


@pytest.mark.asyncio
async def test_create_homework_success(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Tạo bài tập thành công khi thỏa mãn điều kiện tồn tại trên Quiz."""
    fake_quiz_api.set_lesson_metadata(
        "unet-01",
        {
            "slug": "unet-01",
            "name": "Mạng UNet",
            "has_coding": True,
            "has_game": True,
            "coding_count": 1,
            "game_question_count": 5,
            "is_ready": True,
        },
    )
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
    )

    dl = datetime.now(UTC) + timedelta(days=7)
    data = HomeworkCreate(
        title="UNet Project",
        deadline=dl,
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

    # Xác minh lưu thực tế trong In-Memory Repository
    stored_hw = in_memory_homework_repo.get_by_id(saved.id)
    assert stored_hw is not None
    assert stored_hw.slug == "unet-01"

    # Xác minh gán assignees thực tế
    assert in_memory_assignee_repo.get_assigned_user_ids(saved.id) == {1, 2, 3}


@pytest.mark.asyncio
async def test_update_homework_validation(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Cập nhật bài tập: xác thực điều kiện tương tự khi đổi slug hoặc đổi yêu cầu."""
    in_memory_homework_repo.save(
        Homework(
            id=1,
            title="Old title",
            slug="old-slug",
            requires_coding=False,
            requires_game=True,
        )
    )

    fake_quiz_api.set_lesson_metadata(
        "new-slug",
        {
            "slug": "new-slug",
            "name": "New Lesson",
            "has_coding": False,
            "has_game": True,
            "is_ready": True,
        },
    )

    use_case = UpdateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        quiz_api=fake_quiz_api,  # type: ignore
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


@pytest.mark.asyncio
async def test_update_homework_uncheck_game_success(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Cập nhật bài tập: bỏ chọn requires_game thành công khi ban đầu có cả coding và game."""
    in_memory_homework_repo.save(
        Homework(
            id=1,
            title="Existing HW",
            slug="test-slug",
            requires_coding=True,
            requires_game=True,
        )
    )

    fake_quiz_api.set_lesson_metadata(
        "test-slug",
        {
            "slug": "test-slug",
            "name": "Test Lesson",
            "has_coding": True,
            "has_game": False,
            "is_ready": True,
        },
    )

    use_case = UpdateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        quiz_api=fake_quiz_api,  # type: ignore
    )

    result = await use_case.execute(
        homework_id=1,
        data=HomeworkUpdate(
            requires_game=False,
        ),
    )

    assert result.requires_game is False
    assert result.requires_coding is True

    # Xác minh trạng thái lưu thực tế trong RAM
    updated_hw = in_memory_homework_repo.get_by_id(1)
    assert updated_hw is not None
    assert updated_hw.requires_game is False
    assert updated_hw.requires_coding is True


def test_evaluate_submissions_partial_coding():
    """Kiểm tra evaluate_submissions khi học sinh mới làm 1/2 bài coding con."""
    hw = Homework(
        id=1,
        title="Bài tập con test",
        requires_coding=True,
        requires_game=False,
    )
    submissions = [
        HomeworkSubmission(
            id=1,
            homework_id=1,
            user_id=10,
            submission_type=SubmissionType.CODING,
            exercise_id="ex-1",
            is_passed=True,
            submitted_at=datetime.now(UTC),
        )
    ]
    eval_result = hw.evaluate_submissions(
        submissions, required_exercise_ids={"ex-1", "ex-2"}
    )
    assert eval_result.is_submitted is False
    assert eval_result.coding_submitted is False
    assert eval_result.coding_status == "PARTIALLY_SUBMITTED"
    assert eval_result.total_coding_required == 2
    assert eval_result.total_coding_completed == 1
    assert "Còn 1/2 bài tập Coding" in eval_result.uncompleted_items


def test_evaluate_submissions_full_coding():
    """Kiểm tra evaluate_submissions khi học sinh làm đủ cả 2 bài coding con."""
    hw = Homework(
        id=1,
        title="Bài tập con test",
        requires_coding=True,
        requires_game=False,
    )
    submissions = [
        HomeworkSubmission(
            id=1,
            homework_id=1,
            user_id=10,
            submission_type=SubmissionType.CODING,
            exercise_id="ex-1",
            is_passed=True,
            submitted_at=datetime.now(UTC),
        ),
        HomeworkSubmission(
            id=2,
            homework_id=1,
            user_id=10,
            submission_type=SubmissionType.CODING,
            exercise_id="ex-2",
            is_passed=True,
            submitted_at=datetime.now(UTC),
        ),
    ]
    eval_result = hw.evaluate_submissions(
        submissions, required_exercise_ids={"ex-1", "ex-2"}
    )
    assert eval_result.is_submitted is True
    assert eval_result.coding_submitted is True
    assert eval_result.coding_status == "COMPLETED"
    assert eval_result.total_coding_required == 2
    assert eval_result.total_coding_completed == 2
    assert len(eval_result.uncompleted_items) == 0
