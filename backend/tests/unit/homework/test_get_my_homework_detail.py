"""Unit tests for GetMyHomeworkDetailUseCase (US2: personal deadline & SSOT evaluation)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.homework.application.get_my_homework_detail_use_case import (
    GetMyHomeworkDetailUseCase,
)
from app.homework.domain.entity import Homework
from app.homework.domain.value_objects import CompletionStatus, TimelinessStatus
from tests.fixtures.homework_fixtures import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    make_coding_submission,
    make_exercise,
)


@pytest.mark.asyncio
async def test_get_my_homework_detail_uses_personal_deadline_not_class_min(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
):
    """Học viên được gia hạn deadline muộn hơn lớp vẫn nhận đúng deadline cá nhân và ON_TIME."""
    now = datetime.now(UTC)
    class_dl = now - timedelta(days=2)
    extended_dl = now + timedelta(days=2)

    in_memory_homework_repo.save(
        Homework(id=10, title="Đại số tuyến tính", slug="dstt", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.assign_users(10, [1], deadline=class_dl)
    in_memory_assignee_repo.assign_users(10, [2], deadline=extended_dl)
    in_memory_exercise_repo.sync_exercises(
        10,
        [
            make_exercise(10, "ex-1", title="Ma trận", order_index=1),
            make_exercise(10, "ex-2", title="Định thức", order_index=2),
        ],
    )

    # User 2 nộp sau hạn lớp 1 ngày, nhưng TRƯỚC hạn gia hạn cá nhân -> ON_TIME
    sub_time = now - timedelta(days=1)
    in_memory_submission_repo.add_submissions(
        [
            make_coding_submission(10, 2, "ex-1", submitted_at=sub_time, is_passed=True, external_submission_id="u2-1"),
            make_coding_submission(10, 2, "ex-2", submitted_at=sub_time, is_passed=True, external_submission_id="u2-2"),
        ]
    )

    uc = GetMyHomeworkDetailUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )

    detail = await uc.execute(homework_id=10, user_id=2)
    assert detail is not None
    assert detail.homework.deadline == extended_dl
    assert detail.homework.completion_status == CompletionStatus.COMPLETED
    assert detail.homework.timeliness_status == TimelinessStatus.ON_TIME
    assert detail.homework.is_late is False
    assert len(detail.coding_exercises) == 2
    assert all(ex.is_passed and not ex.is_late for ex in detail.coding_exercises)
    assert len(detail.submissions) == 2


@pytest.mark.asyncio
async def test_get_my_homework_detail_returns_none_for_unassigned_user(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
):
    """Trả về None (Controller trả 404) khi học viên không được phân công bài tập."""
    in_memory_homework_repo.save(
        Homework(id=20, title="Private HW", slug="private-hw", requires_coding=True)
    )
    in_memory_assignee_repo.assign_users(20, [1], deadline=datetime.now(UTC) + timedelta(days=1))

    uc = GetMyHomeworkDetailUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )

    assert await uc.execute(homework_id=20, user_id=999) is None
    assert await uc.execute(homework_id=999, user_id=1) is None
