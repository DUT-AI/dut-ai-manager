from datetime import UTC, datetime, timedelta

from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    GameHomeworkSubmission,
    Homework,
    SubmissionType,
)


def test_pure_domain_full_completion_on_time():
    """Học viên nộp đủ cả coding và game trước hạn -> Hoàn thành đầy đủ."""
    deadline = datetime(2026, 11, 20, 23, 59, 59, tzinfo=UTC)
    hw = Homework(
        id=1,
        title="Python Basics",
        requires_coding=True,
        requires_game=True,
    )

    coding_sub = CodingHomeworkSubmission.create_coding(
        homework_id=1,
        user_id=10,
        exercise_id="ex-1",
        submitted_at=deadline - timedelta(hours=2),
        is_passed=True,
    )
    game_sub = GameHomeworkSubmission.create_game(
        homework_id=1,
        user_id=10,
        submitted_at=deadline - timedelta(hours=1),
        is_passed=True,
    )

    eval_result = hw.evaluate_submissions(
        submissions=[coding_sub, game_sub],
        deadline=deadline,
        required_exercise_ids={"ex-1"},
    )

    assert eval_result.is_submitted is True
    assert eval_result.is_overdue is False
    assert eval_result.coding_submitted is True
    assert eval_result.game_submitted is True
    assert eval_result.uncompleted_items == []
    assert eval_result.coding_status == "COMPLETED"


def test_pure_domain_partial_coding_flags_overdue():
    """Yêu cầu 2 bài coding con nhưng chỉ nộp 1 -> Trạng thái PARTIALLY_SUBMITTED và tính quá hạn."""
    deadline = datetime(2026, 11, 10, 23, 59, 59, tzinfo=UTC)
    now_ref = datetime(2026, 11, 11, 8, 0, 0, tzinfo=UTC)
    hw = Homework(
        id=2,
        title="Algorithms",
        requires_coding=True,
        requires_game=False,
    )

    # Chỉ nộp ex-1, thiếu ex-2
    coding_sub = CodingHomeworkSubmission.create_coding(
        homework_id=2,
        user_id=11,
        exercise_id="ex-1",
        submitted_at=deadline - timedelta(hours=5),
        is_passed=True,
    )

    eval_result = hw.evaluate_submissions(
        submissions=[coding_sub],
        deadline=deadline,
        reference_time=now_ref,
        required_exercise_ids={"ex-1", "ex-2"},
    )

    assert eval_result.is_submitted is False
    assert eval_result.is_overdue is True
    assert eval_result.coding_status == "PARTIALLY_SUBMITTED"
    assert eval_result.total_coding_required == 2
    assert eval_result.total_coding_completed == 1
    assert "Còn 1/2 bài tập Coding" in eval_result.uncompleted_items


def test_pure_domain_late_submission_is_not_counted_for_deadline():
    """Bài nộp sau deadline không được tính cho hạn chót, học viên bị phạt quá hạn."""
    deadline = datetime(2026, 11, 10, 23, 59, 59, tzinfo=UTC)
    now_ref = datetime(2026, 11, 11, 8, 0, 0, tzinfo=UTC)
    hw = Homework(
        id=3,
        title="Data Science",
        requires_coding=True,
        requires_game=False,
    )

    # Nộp trễ hạn 1 tiếng
    late_sub = CodingHomeworkSubmission.create_coding(
        homework_id=3,
        user_id=12,
        exercise_id="ex-data",
        submitted_at=deadline + timedelta(hours=1),
        is_passed=True,
    )

    eval_result = hw.evaluate_submissions(
        submissions=[late_sub],
        deadline=deadline,
        reference_time=now_ref,
        required_exercise_ids={"ex-data"},
    )

    assert eval_result.is_submitted is False
    assert eval_result.is_overdue is True


def test_pure_domain_index_submissions_grouping():
    """Kiểm tra Aggregate Root lập chỉ mục bài nộp chính xác theo học viên và bài con."""
    hw = Homework(id=4, title="Indexing Test")

    sub_ex1 = CodingHomeworkSubmission.create_coding(
        homework_id=4,
        user_id=101,
        exercise_id="task-1",
        submitted_at=datetime.now(UTC),
        is_passed=True,
    )
    sub_game = GameHomeworkSubmission.create_game(
        homework_id=4,
        user_id=101,
        submitted_at=datetime.now(UTC),
        is_passed=True,
    )

    ex_map, general_map, game_map = hw.index_submissions([sub_ex1, sub_game])

    assert (101, "task-1") in ex_map
    assert ex_map[(101, "task-1")].submission_type == SubmissionType.CODING
    assert 101 in general_map
    assert 101 in game_map
    assert game_map[101].submission_type == SubmissionType.GAME
