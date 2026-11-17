from datetime import UTC, datetime, timedelta

from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    GameHomeworkSubmission,
    Homework,
    HomeworkExercise,
    SubmissionType,
)
from app.homework.domain.value_objects import CompletionStatus, TimelinessStatus


def _ex(hw_id: int, ex_id: str, order: int = 1, active: bool = True) -> HomeworkExercise:
    return HomeworkExercise(
        homework_id=hw_id,
        exercise_id=ex_id,
        title=f"Exercise {ex_id}",
        order_index=order,
        is_active=active,
    )


def test_pure_domain_full_completion_on_time():
    """Học viên nộp đủ cả coding và game trước hạn -> COMPLETED + ON_TIME."""
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
        required_exercises=[_ex(1, "ex-1")],
        deadline=deadline,
    )

    assert eval_result.completion_status == CompletionStatus.COMPLETED
    assert eval_result.timeliness_status == TimelinessStatus.ON_TIME
    assert eval_result.is_submitted is True
    assert eval_result.is_completed_on_time is True
    assert eval_result.is_late is False
    assert eval_result.is_overdue is False
    assert eval_result.coding_submitted is True
    assert eval_result.game_submitted is True
    assert eval_result.uncompleted_items == []
    assert eval_result.coding_status == "COMPLETED"
    assert eval_result.completed_at == deadline - timedelta(hours=1)


def test_pure_domain_partial_coding_flags_overdue():
    """Yêu cầu 2 bài coding con nhưng chỉ nộp 1 sau hạn -> IN_PROGRESS + OVERDUE."""
    deadline = datetime(2026, 11, 10, 23, 59, 59, tzinfo=UTC)
    now_ref = datetime(2026, 11, 11, 8, 0, 0, tzinfo=UTC)
    hw = Homework(
        id=2,
        title="Algorithms",
        requires_coding=True,
        requires_game=False,
    )

    coding_sub = CodingHomeworkSubmission.create_coding(
        homework_id=2,
        user_id=11,
        exercise_id="ex-1",
        submitted_at=deadline - timedelta(hours=5),
        is_passed=True,
    )

    eval_result = hw.evaluate_submissions(
        submissions=[coding_sub],
        required_exercises=[_ex(2, "ex-1", 1), _ex(2, "ex-2", 2)],
        deadline=deadline,
        reference_time=now_ref,
    )

    assert eval_result.completion_status == CompletionStatus.IN_PROGRESS
    assert eval_result.timeliness_status == TimelinessStatus.OVERDUE
    assert eval_result.is_submitted is False
    assert eval_result.is_completed_on_time is False
    assert eval_result.is_late is False
    assert eval_result.is_overdue is True
    assert eval_result.coding_status == "PARTIALLY_SUBMITTED"
    assert eval_result.total_coding_required == 2
    assert eval_result.total_coding_completed == 1
    assert "Còn 1/2 bài tập Coding" in eval_result.uncompleted_items


def test_pure_domain_late_full_completion_is_completed_late_not_unsubmitted():
    """Hoàn thành 100% sau hạn -> COMPLETED + LATE (is_submitted=True, is_completed_on_time=False)."""
    deadline = datetime(2026, 11, 10, 23, 59, 59, tzinfo=UTC)
    now_ref = datetime(2026, 11, 11, 8, 0, 0, tzinfo=UTC)
    hw = Homework(
        id=3,
        title="Data Science",
        requires_coding=True,
        requires_game=False,
    )

    late_sub = CodingHomeworkSubmission.create_coding(
        homework_id=3,
        user_id=12,
        exercise_id="ex-data",
        submitted_at=deadline + timedelta(hours=1),
        is_passed=True,
    )

    eval_result = hw.evaluate_submissions(
        submissions=[late_sub],
        required_exercises=[_ex(3, "ex-data")],
        deadline=deadline,
        reference_time=now_ref,
    )

    assert eval_result.completion_status == CompletionStatus.COMPLETED
    assert eval_result.timeliness_status == TimelinessStatus.LATE
    assert eval_result.is_submitted is True
    assert eval_result.is_late is True
    assert eval_result.is_overdue is False
    assert eval_result.is_completed_on_time is False
    assert eval_result.coding_is_late is True
    assert eval_result.uncompleted_items == []


def test_pure_domain_resubmit_after_deadline_preserves_on_time():
    """Đã nộp đạt đúng hạn, sau hạn nộp lại (đạt hoặc trượt) -> VẪN giữ COMPLETED + ON_TIME."""
    deadline = datetime(2026, 11, 10, 23, 59, 59, tzinfo=UTC)
    now_ref = datetime(2026, 11, 15, 8, 0, 0, tzinfo=UTC)
    hw = Homework(
        id=4,
        title="Resubmit Test",
        requires_coding=True,
        requires_game=False,
    )

    on_time_pass = CodingHomeworkSubmission.create_coding(
        homework_id=4,
        user_id=20,
        exercise_id="ex-1",
        submitted_at=deadline - timedelta(hours=3),
        is_passed=True,
        score=80.0,
        external_submission_id="sub-1",
    )
    late_fail = CodingHomeworkSubmission.create_coding(
        homework_id=4,
        user_id=20,
        exercise_id="ex-1",
        submitted_at=deadline + timedelta(hours=2),
        is_passed=False,
        score=40.0,
        external_submission_id="sub-2",
    )
    late_better = CodingHomeworkSubmission.create_coding(
        homework_id=4,
        user_id=20,
        exercise_id="ex-1",
        submitted_at=deadline + timedelta(hours=5),
        is_passed=True,
        score=100.0,
        external_submission_id="sub-3",
    )

    eval_result = hw.evaluate_submissions(
        submissions=[on_time_pass, late_fail, late_better],
        required_exercises=[_ex(4, "ex-1")],
        deadline=deadline,
        reference_time=now_ref,
    )

    assert eval_result.completion_status == CompletionStatus.COMPLETED
    assert eval_result.timeliness_status == TimelinessStatus.ON_TIME
    assert eval_result.is_completed_on_time is True
    assert eval_result.is_late is False
    assert eval_result.completed_at == deadline - timedelta(hours=3)
    assert len(eval_result.coding_exercises) == 1
    ex_eval = eval_result.coding_exercises[0]
    assert ex_eval.first_passed_at == deadline - timedelta(hours=3)
    assert ex_eval.latest_submitted_at == deadline + timedelta(hours=5)
    assert ex_eval.best_score == 100.0
    assert ex_eval.attempt_count == 3
    assert ex_eval.is_late is False


def test_pure_domain_ignores_inactive_and_legacy_submissions():
    """Bài con is_active=False hoặc submission lỗi legacy-.../sync-... không làm tăng total_coding_required."""
    deadline = datetime(2026, 11, 20, 23, 59, 59, tzinfo=UTC)
    hw = Homework(id=5, title="Catalog Integrity", requires_coding=True, requires_game=False)

    exercises = [
        _ex(5, "ex-1", order=1, active=True),
        _ex(5, "ex-2", order=2, active=True),
        _ex(5, "ex-removed", order=3, active=False),
    ]
    subs = [
        CodingHomeworkSubmission.create_coding(
            homework_id=5,
            user_id=30,
            exercise_id="ex-1",
            submitted_at=deadline - timedelta(hours=2),
            is_passed=True,
        ),
        CodingHomeworkSubmission.create_coding(
            homework_id=5,
            user_id=30,
            exercise_id="ex-2",
            submitted_at=deadline - timedelta(hours=1),
            is_passed=True,
        ),
        CodingHomeworkSubmission.create_coding(
            homework_id=5,
            user_id=30,
            exercise_id="legacy-5-999",
            submitted_at=deadline - timedelta(hours=4),
            is_passed=True,
        ),
    ]

    eval_result = hw.evaluate_submissions(
        submissions=subs,
        required_exercises=exercises,
        deadline=deadline,
    )

    assert eval_result.completion_status == CompletionStatus.COMPLETED
    assert eval_result.total_coding_required == 2
    assert eval_result.total_coding_completed == 2
    assert [e.exercise_id for e in eval_result.coding_exercises] == ["ex-1", "ex-2"]


def test_pure_domain_not_started_upcoming_vs_overdue():
    """Chưa nộp gì: còn hạn -> NOT_STARTED + UPCOMING; quá hạn -> NOT_STARTED + OVERDUE."""
    deadline = datetime(2026, 11, 20, 23, 59, 59, tzinfo=UTC)
    hw = Homework(id=6, title="Fresh HW", requires_coding=True, requires_game=False)

    upcoming = hw.evaluate_submissions(
        submissions=[],
        required_exercises=[_ex(6, "ex-1")],
        deadline=deadline,
        reference_time=deadline - timedelta(days=1),
    )
    assert upcoming.completion_status == CompletionStatus.NOT_STARTED
    assert upcoming.timeliness_status == TimelinessStatus.UPCOMING
    assert upcoming.is_submitted is False
    assert upcoming.is_overdue is False

    overdue = hw.evaluate_submissions(
        submissions=[],
        required_exercises=[_ex(6, "ex-1")],
        deadline=deadline,
        reference_time=deadline + timedelta(minutes=1),
    )
    assert overdue.completion_status == CompletionStatus.NOT_STARTED
    assert overdue.timeliness_status == TimelinessStatus.OVERDUE
    assert overdue.is_submitted is False
    assert overdue.is_overdue is True


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
