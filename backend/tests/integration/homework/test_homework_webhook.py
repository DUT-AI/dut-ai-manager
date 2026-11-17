from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.homework.application.dtos import (
    HomeworkSubmissionWebhookIn,
    HomeworkWebhookResponse,
)
from app.homework.application.record_submission_use_case import (
    RecordHomeworkSubmissionUseCase,
)
from app.homework.domain.entity import Homework, HomeworkSubmission, SubmissionType
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)


@pytest.fixture
def mock_homework_repo():
    repo = MagicMock(spec=HomeworkRepository)
    return repo


@pytest.fixture
def mock_submission_repo():
    repo = MagicMock(spec=HomeworkSubmissionRepository)
    repo.find_submission_match.return_value = None
    return repo


@pytest.mark.asyncio
async def test_webhook_ignore_external_user(mock_homework_repo, mock_submission_repo):
    """User ngoài nền tảng (user_id >= 1_000_000) sẽ bị bỏ qua."""
    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
    )
    payload = HomeworkSubmissionWebhookIn(
        lesson_slug="batch-normalization",
        user_id=1000005,
        type=SubmissionType.CODING,
        submitted_at=datetime.now(UTC),
    )

    result = await use_case.execute(payload)
    assert isinstance(result, HomeworkWebhookResponse)
    assert result.status == "ignored"
    assert result.reason is not None and "External user" in result.reason
    mock_submission_repo.add_submission.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_ignore_nonexistent_homework(
    mock_homework_repo, mock_submission_repo
):
    """Bài tập không tồn tại theo slug sẽ bị bỏ qua."""
    mock_homework_repo.get_by_slug = MagicMock(return_value=None)
    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
    )
    payload = HomeworkSubmissionWebhookIn(
        lesson_slug="nonexistent-slug",
        user_id=12,
        type=SubmissionType.CODING,
        submitted_at=datetime.now(UTC),
    )

    result = await use_case.execute(payload)
    assert isinstance(result, HomeworkWebhookResponse)
    assert result.status == "ignored"
    assert result.reason is not None and "Homework not found" in result.reason
    mock_submission_repo.add_submission.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_record_coding_submission_success(
    mock_homework_repo, mock_submission_repo
):
    """Ghi nhận thành công bài nộp coding của học viên nội bộ."""
    hw = Homework(
        id=1,
        title="Batch Normalization",
        slug="batch-norm",
        deadline=datetime.now(UTC),
        requires_coding=True,
    )
    mock_homework_repo.get_by_slug = MagicMock(return_value=hw)

    def fake_add(submission):
        submission.id = 99
        return submission

    mock_submission_repo.add_submission = MagicMock(side_effect=fake_add)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
    )
    now_time = datetime.now(UTC)
    payload = HomeworkSubmissionWebhookIn(
        lesson_slug="batch-norm",
        user_id=42,
        type=SubmissionType.CODING,
        submitted_at=now_time,
        details={"quiz_submission_id": "abc-123"},
    )

    result = await use_case.execute(payload)
    assert isinstance(result, HomeworkWebhookResponse)
    assert result.status == "recorded"
    assert result.submission_id == 99
    assert result.homework_id == 1
    assert result.user_id == 42
    mock_submission_repo.add_submission.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_record_game_submission_success(
    mock_homework_repo, mock_submission_repo
):
    """Ghi nhận thành công lượt chơi game 100% của học viên nội bộ."""
    hw = Homework(
        id=2,
        title="Game Optimization",
        slug="game-opt",
        deadline=datetime.now(UTC),
        requires_game=True,
    )
    mock_homework_repo.get_by_slug = MagicMock(return_value=hw)

    def fake_add(submission):
        submission.id = 100
        return submission

    mock_submission_repo.add_submission = MagicMock(side_effect=fake_add)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
    )
    payload = HomeworkSubmissionWebhookIn(
        lesson_slug="game-opt",
        user_id=15,
        type=SubmissionType.GAME,
        submitted_at=datetime.now(UTC),
        is_passed=True,
        details={"final_score": 100.0},
    )

    result = await use_case.execute(payload)
    assert isinstance(result, HomeworkWebhookResponse)
    assert result.status == "recorded"
    assert result.submission_id == 100
    mock_submission_repo.add_submission.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_homework_submissions_use_case(mock_submission_repo):
    """Kiểm tra lấy danh sách lịch sử bài nộp qua GetUserHomeworkSubmissionsUseCase."""
    from app.homework.application.get_user_homework_submissions_use_case import (
        GetUserHomeworkSubmissionsUseCase,
    )

    now_time = datetime.now(UTC)
    mock_submission_repo.get_submissions_by_user.return_value = [
        HomeworkSubmission(
            id=1,
            homework_id=10,
            user_id=5,
            submission_type=SubmissionType.CODING,
            submitted_at=now_time,
            is_passed=True,
            details={"attempt": 1},
        ),
        HomeworkSubmission(
            id=2,
            homework_id=10,
            user_id=5,
            submission_type=SubmissionType.GAME,
            submitted_at=now_time,
            is_passed=True,
            details={"final_score": 100.0},
        ),
    ]

    use_case = GetUserHomeworkSubmissionsUseCase(
        homework_submission_repo=mock_submission_repo
    )
    result = await use_case.execute(homework_id=10, user_id=5)

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].submission_type == SubmissionType.CODING
    assert result[1].id == 2
    assert result[1].submission_type == SubmissionType.GAME
    mock_submission_repo.get_submissions_by_user.assert_called_once_with(10, 5)


@pytest.mark.asyncio
async def test_webhook_record_exercise_submission_with_details(
    mock_homework_repo, mock_submission_repo
):
    """Ghi nhận thành công bài nộp kèm exercise_id và exercise_title."""
    hw = Homework(
        id=5,
        title="Deep Learning Lab",
        slug="dl-lab",
        deadline=datetime.now(UTC),
        requires_coding=True,
    )
    mock_homework_repo.get_by_slug = MagicMock(return_value=hw)
    mock_submission_repo.find_submission_match = MagicMock(return_value=None)

    def fake_add(submission):
        submission.id = 101
        return submission

    mock_submission_repo.add_submission = MagicMock(side_effect=fake_add)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
    )
    payload = HomeworkSubmissionWebhookIn(
        lesson_slug="dl-lab",
        user_id=42,
        type=SubmissionType.CODING,
        submitted_at=datetime.now(UTC),
        exercise_id="uuid-ex-1",
        exercise_title="Bài tập 1: Cài đặt CNN",
        submission_id="sub-uuid-1",
        attempt_number=1,
        score=95.0,
        original_filename="cnn.py",
        is_passed=True,
    )

    result = await use_case.execute(payload)
    assert result["status"] == "recorded"
    assert result["submission_id"] == 101
    assert result["exercise_id"] == "uuid-ex-1"
    mock_submission_repo.add_submission.assert_called_once()
    added_sub = mock_submission_repo.add_submission.call_args[0][0]
    assert added_sub.exercise_id == "uuid-ex-1"
    assert added_sub.exercise_title == "Bài tập 1: Cài đặt CNN"
    assert added_sub.score == 95.0


@pytest.mark.asyncio
async def test_webhook_update_existing_exercise_submission(
    mock_homework_repo, mock_submission_repo
):
    """Cập nhật bản ghi khi nộp lại bài tập con (Idempotent update)."""
    hw = Homework(
        id=5,
        title="Deep Learning Lab",
        slug="dl-lab",
        deadline=datetime.now(UTC),
        requires_coding=True,
    )
    mock_homework_repo.get_by_slug = MagicMock(return_value=hw)
    existing_model = MagicMock()
    existing_model.id = 101
    mock_submission_repo.find_submission_match = MagicMock(return_value=existing_model)

    updated_entity = HomeworkSubmission(
        id=101,
        homework_id=5,
        user_id=42,
        submission_type=SubmissionType.CODING,
        exercise_id="uuid-ex-1",
        exercise_title="Bài tập 1: Cài đặt CNN",
        score=100.0,
        attempt_number=2,
        submitted_at=datetime.now(UTC),
        is_passed=True,
    )
    mock_submission_repo.update_submission = MagicMock(return_value=updated_entity)

    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=mock_homework_repo,
        homework_submission_repo=mock_submission_repo,
    )
    payload = HomeworkSubmissionWebhookIn(
        lesson_slug="dl-lab",
        user_id=42,
        type=SubmissionType.CODING,
        submitted_at=datetime.now(UTC),
        exercise_id="uuid-ex-1",
        exercise_title="Bài tập 1: Cài đặt CNN",
        submission_id="sub-uuid-2",
        attempt_number=2,
        score=100.0,
        original_filename="cnn_v2.py",
        is_passed=True,
    )

    result = await use_case.execute(payload)
    assert result["status"] == "updated"
    assert result["submission_id"] == 101
    assert result["exercise_id"] == "uuid-ex-1"
    mock_submission_repo.update_submission.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_append_only_preserves_earlier_submission_timestamp():
    """
    US5: Nộp lần 1 (submission_id=sub-1) trước hạn, sau hạn nộp lại (submission_id=sub-2)
    cùng exercise_id -> lưu 2 bản ghi riêng biệt, KHÔNG ghi đè submitted_at của lần 1;
    gửi lặp submission_id=sub-2 -> idempotent update không tạo bản ghi thứ 3.
    """
    from datetime import timedelta

    from app.homework.infrastructure.in_memory import (
        InMemoryHomeworkRepository,
        InMemoryHomeworkSubmissionRepository,
    )

    hw_repo = InMemoryHomeworkRepository(
        [Homework(id=5, title="Deep Learning Lab", slug="dl-lab", requires_coding=True)]
    )
    sub_repo = InMemoryHomeworkSubmissionRepository()
    use_case = RecordHomeworkSubmissionUseCase(
        homework_repo=hw_repo,
        homework_submission_repo=sub_repo,
    )

    t1 = datetime(2026, 11, 10, 10, 0, 0, tzinfo=UTC)
    t2 = t1 + timedelta(days=2)

    r1 = await use_case.execute(
        HomeworkSubmissionWebhookIn(
            lesson_slug="dl-lab",
            user_id=42,
            type=SubmissionType.CODING,
            submitted_at=t1,
            exercise_id="uuid-ex-1",
            submission_id="sub-1",
            score=90.0,
            is_passed=True,
        )
    )
    r2 = await use_case.execute(
        HomeworkSubmissionWebhookIn(
            lesson_slug="dl-lab",
            user_id=42,
            type=SubmissionType.CODING,
            submitted_at=t2,
            exercise_id="uuid-ex-1",
            submission_id="sub-2",
            score=100.0,
            is_passed=True,
        )
    )
    r2_dup = await use_case.execute(
        HomeworkSubmissionWebhookIn(
            lesson_slug="dl-lab",
            user_id=42,
            type=SubmissionType.CODING,
            submitted_at=t2,
            exercise_id="uuid-ex-1",
            submission_id="sub-2",
            score=100.0,
            is_passed=True,
        )
    )

    assert r1.status == "recorded"
    assert r2.status == "recorded"
    assert r2_dup.status == "updated"
    assert r1.submission_id != r2.submission_id
    assert r2_dup.submission_id == r2.submission_id

    all_subs = sub_repo.get_submissions_by_user(5, 42)
    assert len(all_subs) == 2
    assert {s.submitted_at for s in all_subs} == {t1, t2}
