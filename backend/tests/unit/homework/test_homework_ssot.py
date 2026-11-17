"""SSOT consistency tests across all 4 homework views (Home, MyHomeworks, MyDetail, Admin Status)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.homework.application.get_homework_submission_status_use_case import (
    GetHomeworkSubmissionStatusUseCase,
)
from app.homework.application.get_my_homework_detail_use_case import (
    GetMyHomeworkDetailUseCase,
)
from app.homework.application.get_unsubmitted_homeworks_for_user_use_case import (
    GetUnsubmittedHomeworksForUserUseCase,
)
from app.homework.application.get_user_homeworks_use_case import (
    GetUserHomeworksUseCase,
)
from app.homework.application.helpers import QuizSubmissionHelper
from app.homework.domain.entity import Homework
from app.homework.domain.value_objects import (
    AssigneeUserInfo,
    CompletionStatus,
    TimelinessStatus,
)
from tests.fixtures.homework_fixtures import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    make_coding_submission,
    make_exercise,
    make_game_submission,
)


def test_homework_extract_slug_and_effective_slug():
    """Entity Homework là SSOT chịu trách nhiệm trích xuất slug hiệu lực."""
    hw1 = Homework(
        title="HW 1",
        slug="  bai-hoc-1  ",
        link="https://quiz.ai/lessons/bai-hoc-cu",
    )
    assert hw1.effective_slug == "bai-hoc-1"
    assert Homework.extract_slug(hw1.link, hw1.slug) == "bai-hoc-1"

    hw2 = Homework(
        title="HW 2",
        slug="",
        link="https://example.com/homeworks/bai-tap-oop?tab=1#top",
    )
    assert hw2.effective_slug == "bai-tap-oop"

    hw3 = Homework(title="HW 3", link="https://quiz.example.com/game/quiz-01/")
    assert hw3.effective_slug == "quiz-01"

    assert QuizSubmissionHelper.extract_slug_from_entity(hw2) == "bai-tap-oop"
    assert QuizSubmissionHelper.extract_slug(hw1.link, hw1.slug) == "bai-hoc-1"


@pytest.mark.asyncio
async def test_four_views_are_100_percent_consistent_for_late_and_partial_students(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
):
    """
    Xác minh 0% sai lệch giữa 4 luồng:
    - HomePage (GetUnsubmittedHomeworksForUserUseCase)
    - MyHomeworks (GetUserHomeworksUseCase)
    - MyHomeworkDetail (GetMyHomeworkDetailUseCase)
    - Admin Status (GetHomeworkSubmissionStatusUseCase)
    """

    class FakeUserRepo:
        pass

    now = datetime.now(UTC)
    past_dl = now - timedelta(days=1)

    hw = Homework(
        id=50,
        title="Bài tập Python Full",
        requires_coding=True,
        requires_game=True,
        slug="python-full",
    )
    in_memory_homework_repo.add(hw)
    in_memory_exercise_repo.sync_exercises(
        50,
        [
            make_exercise(50, "ex-1", title="Bài 1", order_index=1),
            make_exercise(50, "ex-2", title="Bài 2", order_index=2),
        ],
    )

    in_memory_assignee_repo.set_assignees(
        50,
        [
            AssigneeUserInfo(user_id=1, name="HS 1 (Xong trễ)", deadline=past_dl, avatar_url=None),
            AssigneeUserInfo(user_id=2, name="HS 2 (Làm dở 1/2)", deadline=past_dl, avatar_url=None),
            AssigneeUserInfo(user_id=3, name="HS 3 (Chỉ xong Game)", deadline=past_dl, avatar_url=None),
        ],
        default_deadline=past_dl,
    )

    in_memory_submission_repo.add_submissions(
        [
            # User 1: hoàn thành 100% cả 2 bài coding + game SAU hạn -> COMPLETED + LATE
            make_coding_submission(50, 1, "ex-1", submitted_at=past_dl + timedelta(hours=1), is_passed=True, external_submission_id="u1-1"),
            make_coding_submission(50, 1, "ex-2", submitted_at=past_dl + timedelta(hours=2), is_passed=True, external_submission_id="u1-2"),
            make_game_submission(50, 1, submitted_at=past_dl + timedelta(hours=3), is_passed=True, external_submission_id="u1-g"),
            # User 2: chỉ nộp 1/2 bài coding, chưa chơi game
            make_coding_submission(50, 2, "ex-1", submitted_at=past_dl - timedelta(hours=2), is_passed=True, external_submission_id="u2-1"),
            # User 3: chỉ xong game, chưa nộp coding
            make_game_submission(50, 3, submitted_at=past_dl - timedelta(hours=1), is_passed=True, external_submission_id="u3-g"),
        ]
    )

    unsub_uc = GetUnsubmittedHomeworksForUserUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )
    my_list_uc = GetUserHomeworksUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )
    my_detail_uc = GetMyHomeworkDetailUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )
    admin_status_uc = GetHomeworkSubmissionStatusUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        user_repo=FakeUserRepo(),  # type: ignore
    )

    admin_res = await admin_status_uc.execute(50)
    assert admin_res is not None
    assert admin_res.total_completed_count == 1
    admin_by_uid = {s.user_id: s for s in admin_res.students}

    # Kiểm tra User 1 (hoàn thành 100% sau hạn): KHÔNG xuất hiện ở unsubmitted, cả 4 nơi báo COMPLETED (2/2)
    assert await unsub_uc.execute(1) == []
    u1_list, _ = await my_list_uc.execute(1)
    u1_detail = await my_detail_uc.execute(50, 1)
    assert u1_detail is not None
    assert u1_list.items[0].completion_status == CompletionStatus.COMPLETED
    assert u1_list.items[0].timeliness_status == TimelinessStatus.LATE
    assert u1_detail.homework.completion_status == CompletionStatus.COMPLETED
    assert u1_detail.homework.timeliness_status == TimelinessStatus.LATE
    assert admin_by_uid[1].coding_status == "COMPLETED"
    assert admin_by_uid[1].game_is_submitted is True
    assert admin_by_uid[1].coding_is_late is True

    # Kiểm tra User 2 (làm dở 1/2): cả 4 nơi đều khớp 1/2 và chưa hoàn thành
    u2_unsub = await unsub_uc.execute(2)
    u2_list, _ = await my_list_uc.execute(2)
    u2_detail = await my_detail_uc.execute(50, 2)
    assert len(u2_unsub) == 1
    assert u2_unsub[0].total_coding_completed == 1 and u2_unsub[0].total_coding_required == 2
    assert u2_list.items[0].total_coding_completed == 1 and u2_list.items[0].total_coding_required == 2
    assert u2_detail is not None and u2_detail.homework.total_coding_completed == 1
    assert admin_by_uid[2].total_coding_completed == 1 and admin_by_uid[2].total_coding_required == 2
