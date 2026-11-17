"""Unit tests for GetUserHomeworksUseCase and SyncMyUnsubmittedHomeworksUseCase (US1 & US4)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.homework.application.get_user_homeworks_use_case import (
    GetUserHomeworksUseCase,
)
from app.homework.application.sync_homework_use_case import (
    SyncHomeworkFromQuizUseCase,
)
from app.homework.application.sync_my_unsubmitted_homeworks_use_case import (
    SyncMyUnsubmittedHomeworksUseCase,
)
from app.homework.domain.entity import Homework
from app.homework.domain.value_objects import CompletionStatus, TimelinessStatus
from tests.fixtures.homework_fixtures import (
    FakeQuizApiClient,
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
    make_coding_submission,
    make_exercise,
)


@pytest.mark.asyncio
async def test_get_user_homeworks_partial_and_full_and_late_completion(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
):
    """Kiểm chứng đủ các trạng thái 2 chiều: ON_TIME, LATE, IN_PROGRESS, NOT_STARTED, OVERDUE."""
    now = datetime.now(UTC)
    past_dl = now - timedelta(days=3)
    future_dl = now + timedelta(days=3)

    # HW 1: Hoàn thành đúng hạn + nộp lại sau hạn -> vẫn COMPLETED + ON_TIME
    hw1 = in_memory_homework_repo.save(
        Homework(id=1, title="HW On Time", slug="hw-1", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.assign_users(1, [10], deadline=past_dl)
    in_memory_exercise_repo.sync_exercises(1, [make_exercise(1, "ex-1", order_index=1)])
    in_memory_submission_repo.add_submissions(
        [
            make_coding_submission(1, 10, "ex-1", submitted_at=past_dl - timedelta(hours=2), is_passed=True, external_submission_id="s1"),
            make_coding_submission(1, 10, "ex-1", submitted_at=past_dl + timedelta(hours=5), is_passed=True, external_submission_id="s2"),
        ]
    )

    # HW 2: Hoàn thành 100% sau hạn -> COMPLETED + LATE (is_submitted=True, is_overdue=False)
    in_memory_homework_repo.save(
        Homework(id=2, title="HW Completed Late", slug="hw-2", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.assign_users(2, [10], deadline=past_dl)
    in_memory_exercise_repo.sync_exercises(2, [make_exercise(2, "ex-a", order_index=1), make_exercise(2, "ex-b", order_index=2)])
    in_memory_submission_repo.add_submissions(
        [
            make_coding_submission(2, 10, "ex-a", submitted_at=past_dl + timedelta(hours=1), is_passed=True, external_submission_id="s3"),
            make_coding_submission(2, 10, "ex-b", submitted_at=past_dl + timedelta(hours=2), is_passed=True, external_submission_id="s4"),
        ]
    )

    # HW 3: Làm dở 1/2 bài con (còn hạn) -> IN_PROGRESS + UPCOMING
    in_memory_homework_repo.save(
        Homework(id=3, title="HW Partial Upcoming", slug="hw-3", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.assign_users(3, [10], deadline=future_dl)
    in_memory_exercise_repo.sync_exercises(3, [make_exercise(3, "ex-1", order_index=1), make_exercise(3, "ex-2", order_index=2)])
    in_memory_submission_repo.add(
        make_coding_submission(3, 10, "ex-1", submitted_at=now - timedelta(hours=1), is_passed=True, external_submission_id="s5")
    )

    # HW 4: Chưa làm và quá hạn -> NOT_STARTED + OVERDUE
    in_memory_homework_repo.save(
        Homework(id=4, title="HW Overdue", slug="hw-4", requires_coding=True, requires_game=False)
    )
    in_memory_assignee_repo.assign_users(4, [10], deadline=past_dl)
    in_memory_exercise_repo.sync_exercises(4, [make_exercise(4, "ex-1", order_index=1)])

    use_case = GetUserHomeworksUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )

    page_data, total = await use_case.execute(user_id=10, page=1, page_size=20)
    assert total == 4
    assert page_data.stats.total == 4
    assert page_data.stats.completed == 2
    assert page_data.stats.completed_on_time == 1
    assert page_data.stats.completed_late == 1
    assert page_data.stats.uncompleted == 2
    assert page_data.stats.overdue == 1

    by_id = {item.id: item for item in page_data.items}
    assert by_id[hw1.id].completion_status == CompletionStatus.COMPLETED
    assert by_id[hw1.id].timeliness_status == TimelinessStatus.ON_TIME
    assert by_id[hw1.id].is_submitted is True
    assert by_id[hw1.id].is_late is False

    assert by_id[2].completion_status == CompletionStatus.COMPLETED
    assert by_id[2].timeliness_status == TimelinessStatus.LATE
    assert by_id[2].is_submitted is True
    assert by_id[2].is_late is True
    assert by_id[2].is_overdue is False

    assert by_id[3].completion_status == CompletionStatus.IN_PROGRESS
    assert by_id[3].timeliness_status == TimelinessStatus.UPCOMING
    assert by_id[3].is_submitted is False
    assert by_id[3].total_coding_required == 2
    assert by_id[3].total_coding_completed == 1
    assert "Còn 1/2 bài tập Coding" in by_id[3].uncompleted_items

    assert by_id[4].completion_status == CompletionStatus.NOT_STARTED
    assert by_id[4].timeliness_status == TimelinessStatus.OVERDUE
    assert by_id[4].is_overdue is True


@pytest.mark.asyncio
async def test_get_user_homeworks_server_pagination_filtering_and_search(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
):
    """Kiểm chứng 30 bài tập: phân trang trang 1/2, stats tổng bất biến khi lọc/tìm kiếm, tìm được bài ở trang 2."""
    now = datetime.now(UTC)
    future_dl = now + timedelta(days=5)
    past_dl = now - timedelta(days=2)

    for idx in range(1, 31):
        title = "Gen2: Xác suất đặc biệt" if idx == 25 else f"Bài tập số {idx:02d}"
        in_memory_homework_repo.save(
            Homework(id=idx, title=title, slug=f"hw-{idx}", requires_coding=True, requires_game=False)
        )
        in_memory_exercise_repo.sync_exercises(idx, [make_exercise(idx, f"ex-{idx}", order_index=1)])
        if idx <= 20:
            # 20 bài đã hoàn thành đúng hạn
            in_memory_assignee_repo.assign_users(idx, [7], deadline=future_dl)
            in_memory_submission_repo.add(
                make_coding_submission(idx, 7, f"ex-{idx}", submitted_at=now - timedelta(hours=1), is_passed=True)
            )
        elif idx <= 27:
            # 7 bài chưa hoàn thành, còn hạn (gồm bài #25)
            in_memory_assignee_repo.assign_users(idx, [7], deadline=future_dl)
        else:
            # 3 bài quá hạn chưa hoàn thành (#28, #29, #30)
            in_memory_assignee_repo.assign_users(idx, [7], deadline=past_dl)

    use_case = GetUserHomeworksUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )

    # Trang 1 & Trang 2
    p1, total1 = await use_case.execute(user_id=7, page=1, page_size=20, status="all")
    p2, total2 = await use_case.execute(user_id=7, page=2, page_size=20, status="all")
    assert total1 == 30 and len(p1.items) == 20
    assert total2 == 30 and len(p2.items) == 10
    assert p1.stats.total == 30 and p2.stats.total == 30
    assert p1.stats.completed == 20 and p1.stats.uncompleted == 10 and p1.stats.overdue == 3

    # Lọc uncompleted -> stats tổng vẫn = 30, kết quả lọc = 10
    uncomp, uncomp_total = await use_case.execute(user_id=7, page=1, page_size=20, status="uncompleted")
    assert uncomp_total == 10
    assert len(uncomp.items) == 10
    assert uncomp.stats.total == 30

    # Lọc overdue -> 3 bài
    ov, ov_total = await use_case.execute(user_id=7, page=1, page_size=20, status="overdue")
    assert ov_total == 3
    assert {item.id for item in ov.items} == {28, 29, 30}

    # Tìm kiếm bài #25 (nằm ở trang 2) không phân biệt hoa thường
    searched, s_total = await use_case.execute(
        user_id=7, page=1, page_size=20, status="all", search="XÁC SUẤT ĐẶC BIỆT"
    )
    assert s_total == 1
    assert searched.items[0].id == 25
    assert searched.stats.total == 30


@pytest.mark.asyncio
async def test_sync_my_unsubmitted_homeworks_respects_limit_and_failsafe(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_submission_repo: InMemoryHomeworkSubmissionRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
    fake_quiz_api: FakeQuizApiClient,
):
    """SyncMyUnsubmittedHomeworksUseCase chỉ đồng bộ bài chưa COMPLETED, giới hạn tối đa 10 bài/lượt."""
    future_dl = datetime.now(UTC) + timedelta(days=3)

    # Tạo 12 bài chưa hoàn thành + 1 bài đã hoàn thành
    for idx in range(1, 14):
        slug = f"lesson-{idx}"
        in_memory_homework_repo.save(
            Homework(id=idx, title=f"Lesson {idx}", slug=slug, requires_coding=True, requires_game=False)
        )
        in_memory_assignee_repo.assign_users(idx, [55], deadline=future_dl)
        in_memory_exercise_repo.sync_exercises(idx, [make_exercise(idx, f"ex-{idx}", order_index=1)])
        fake_quiz_api.set_lesson_exercises(slug, [{"id": f"ex-{idx}", "title": f"Ex {idx}"}])

    # Bài #1 đã hoàn thành -> phải được bỏ qua khi sync
    in_memory_submission_repo.add(
        make_coding_submission(1, 55, "ex-1", submitted_at=datetime.now(UTC), is_passed=True)
    )

    sync_hw_uc = SyncHomeworkFromQuizUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        quiz_api=fake_quiz_api,  # type: ignore
    )
    sync_my_uc = SyncMyUnsubmittedHomeworksUseCase(
        homework_repo=in_memory_homework_repo,
        homework_submission_repo=in_memory_submission_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
        sync_homework_uc=sync_hw_uc,
    )

    result = await sync_my_uc.execute(user_id=55)
    assert result.total_checked == 10
    assert result.synced_count == 10
    assert result.failed_count == 0
    assert all(r.homework_id != 1 for r in result.results)
