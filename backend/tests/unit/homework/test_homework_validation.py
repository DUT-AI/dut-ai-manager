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
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    make_exercise,
)


@pytest.mark.asyncio
async def test_create_homework_rejects_when_no_options_selected(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
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
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    fake_quiz_api.set_lesson_metadata("lesson-khong-ton-tai", None)  # type: ignore
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
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
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
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
        homework_exercise_repo=in_memory_exercise_repo,
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
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
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
        homework_exercise_repo=in_memory_exercise_repo,
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
async def test_create_homework_success_initializes_official_exercises(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """Tạo bài tập thành công và khởi tạo ngay danh mục homework_exercises chính thức."""
    fake_quiz_api.set_lesson_metadata(
        "unet-01",
        {
            "slug": "unet-01",
            "name": "Mạng UNet",
            "has_coding": True,
            "has_game": True,
            "coding_count": 2,
            "game_question_count": 5,
            "is_ready": True,
        },
    )
    fake_quiz_api.set_lesson_exercises(
        "unet-01",
        [
            {"id": "unet-ex-1", "title": "Encoder"},
            {"id": "unet-ex-2", "title": "Decoder"},
        ],
    )
    use_case = CreateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        quiz_api=fake_quiz_api,  # type: ignore
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
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
    assert saved.last_synced_at is not None
    assert in_memory_assignee_repo.get_assigned_user_ids(saved.id) == {1, 2, 3}
    active_exs = in_memory_exercise_repo.get_active_by_homework(saved.id)
    assert [e.exercise_id for e in active_exs] == ["unet-ex-1", "unet-ex-2"]


@pytest.mark.asyncio
async def test_update_homework_validation(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
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
        homework_exercise_repo=in_memory_exercise_repo,
        quiz_api=fake_quiz_api,  # type: ignore
    )

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
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
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
    fake_quiz_api.set_lesson_exercises("test-slug", [{"id": "ex-1", "title": "Ex 1"}])

    use_case = UpdateHomeworkUseCase(
        homework_repo=in_memory_homework_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        quiz_api=fake_quiz_api,  # type: ignore
    )

    result = await use_case.execute(
        homework_id=1,
        data=HomeworkUpdate(requires_game=False),
    )

    assert result.requires_game is False
    assert result.requires_coding is True
    assert [e.exercise_id for e in in_memory_exercise_repo.get_active_by_homework(1)] == ["ex-1"]


def test_evaluate_submissions_partial_coding():
    hw = Homework(id=1, title="Bài tập con test", requires_coding=True, requires_game=False)
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
        submissions,
        required_exercises=[make_exercise(1, "ex-1", order_index=1), make_exercise(1, "ex-2", order_index=2)],
    )
    assert eval_result.is_submitted is False
    assert eval_result.coding_submitted is False
    assert eval_result.coding_status == "PARTIALLY_SUBMITTED"
    assert eval_result.total_coding_required == 2
    assert eval_result.total_coding_completed == 1
    assert "Còn 1/2 bài tập Coding" in eval_result.uncompleted_items


def test_evaluate_submissions_full_coding():
    hw = Homework(id=1, title="Bài tập con test", requires_coding=True, requires_game=False)
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
        submissions,
        required_exercises=[make_exercise(1, "ex-1", order_index=1), make_exercise(1, "ex-2", order_index=2)],
    )
    assert eval_result.is_submitted is True
    assert eval_result.coding_submitted is True
    assert eval_result.coding_status == "COMPLETED"
    assert eval_result.total_coding_required == 2
    assert eval_result.total_coding_completed == 2
    assert len(eval_result.uncompleted_items) == 0
