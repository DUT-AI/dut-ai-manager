from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.meeting.application.get_my_evaluation_result_use_case import (
    GetMyEvaluationResultUseCase,
)
from app.meeting.application.submit_trainee_evaluation_use_case import (
    SubmitTraineeEvaluationUseCase,
)
from app.meeting.application.submit_trainer_evaluation_use_case import (
    SubmitTrainerEvaluationUseCase,
)
from app.meeting.domain.entity import (
    Meeting,
    MeetingParticipant,
)
from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.shared.application.response import BadRequestException


@pytest.mark.asyncio
async def test_submit_trainer_evaluation_success():
    meeting_repo = MagicMock()
    eval_repo = MagicMock()

    past_start = datetime.now() - timedelta(hours=3)
    past_end = datetime.now() - timedelta(hours=1)

    mock_meeting = Meeting(
        id=1,
        title="Python 101",
        start_time=past_start,
        end_time=past_end,
        enable_evaluation=True,
        created_by=10,
        participants=[MeetingParticipant(user_id=20, status=ParticipantStatus.JOINED)],
    )
    meeting_repo.get_by_id.return_value = mock_meeting
    eval_repo.get_by_meeting_and_users.return_value = None
    eval_repo.save.side_effect = lambda x: x

    use_case = SubmitTrainerEvaluationUseCase(meeting_repo, eval_repo)
    scores_data = [
        {"criteria_code": "TRAINER_TO_TRAINEE_ATTENDANCE", "score": 5},
        {"criteria_code": "TRAINER_TO_TRAINEE_INTERACTION", "score": 4},
        {"criteria_code": "TRAINER_TO_TRAINEE_COMPREHENSION", "score": 4},
        {"criteria_code": "TRAINER_TO_TRAINEE_PREPARATION", "score": 5},
    ]

    result = await use_case.execute(
        meeting_id=1,
        reviewer_id=10,
        target_user_id=20,
        scores_data=scores_data,
        feedback_text="Làm bài rất tốt",
    )

    assert result.meeting_id == 1
    assert result.reviewer_id == 10
    assert result.target_user_id == 20
    assert result.average_score == 4.5
    assert result.evaluation_type == EvaluationType.TRAINER_TO_TRAINEE


@pytest.mark.asyncio
async def test_submit_trainee_evaluation_anonymous():
    meeting_repo = MagicMock()
    eval_repo = MagicMock()

    past_start = datetime.now() - timedelta(hours=3)
    past_end = datetime.now() - timedelta(hours=1)

    mock_meeting = Meeting(
        id=1,
        title="Python 101",
        start_time=past_start,
        end_time=past_end,
        enable_evaluation=True,
        created_by=10,
        participants=[MeetingParticipant(user_id=20, status=ParticipantStatus.JOINED)],
    )
    meeting_repo.get_by_id.return_value = mock_meeting
    eval_repo.get_by_meeting_and_users.return_value = None
    eval_repo.save.side_effect = lambda x: x

    use_case = SubmitTraineeEvaluationUseCase(meeting_repo, eval_repo)
    scores_data = [
        {"criteria_code": "TRAINEE_TO_TRAINER_CONTENT", "score": 5},
        {"criteria_code": "TRAINEE_TO_TRAINER_METHOD", "score": 5},
        {"criteria_code": "TRAINEE_TO_TRAINER_ATMOSPHERE", "score": 5},
        {"criteria_code": "TRAINEE_TO_TRAINER_VALUE", "score": 5},
    ]

    result = await use_case.execute(
        meeting_id=1,
        reviewer_id=20,
        target_user_id=10,
        scores_data=scores_data,
        is_anonymous=True,
        feedback_text="Thầy giảng rất hay",
    )

    assert result.is_anonymous is True
    assert result.reviewer_id == 20
    assert result.average_score == 5.0


@pytest.mark.asyncio
async def test_get_my_evaluation_result_locked_until_evaluated():
    meeting_repo = MagicMock()
    eval_repo = MagicMock()

    mock_meeting = Meeting(
        id=1,
        title="Python 101",
        start_time=datetime.now() - timedelta(hours=3),
        end_time=datetime.now() - timedelta(hours=1),
        enable_evaluation=True,
        created_by=10,
    )
    meeting_repo.get_by_id.return_value = mock_meeting
    # Trainee chưa đánh giá Trainer
    eval_repo.get_by_meeting_and_users.return_value = None
    eval_repo.get_evaluations_by_meeting.return_value = []

    use_case = GetMyEvaluationResultUseCase(meeting_repo, eval_repo)

    with pytest.raises(BadRequestException) as exc_info:
        await use_case.execute(meeting_id=1, current_user_id=20)

    assert exc_info.value.status_code == 403


def test_evaluation_criterion_value_object():
    from app.meeting.domain.value_objects import (
        EvaluationCriteriaCode,
        EvaluationCriterion,
        EvaluationType,
    )

    # 1. Mã chuẩn
    c1 = EvaluationCriterion.from_code(EvaluationCriteriaCode.ATTENDANCE_CONDUCT)
    assert c1.code == "ATTENDANCE_CONDUCT"
    assert c1.name == "Chuyên cần & Tác phong"
    assert c1.evaluation_type == EvaluationType.TRAINER_TO_TRAINEE

    # 2. Mã có prefix cũ
    c2 = EvaluationCriterion.from_code("TRAINEE_TO_TRAINER_CONTENT")
    assert c2.code == "TRAINEE_TO_TRAINER_CONTENT"
    assert c2.name == "Chất lượng Nội dung bài học"
    assert c2.evaluation_type == EvaluationType.TRAINEE_TO_TRAINER


@pytest.mark.asyncio
async def test_get_meeting_evaluation_summary_use_case():
    from app.meeting.application.get_meeting_evaluation_summary_use_case import (
        GetMeetingEvaluationSummaryUseCase,
    )
    from app.meeting.domain.entity import EvaluationScoreItem, MeetingEvaluation

    meeting_repo = MagicMock()
    eval_repo = MagicMock()

    mock_meeting = Meeting(
        id=10,
        title="Architecture Workshop",
        start_time=datetime.now() - timedelta(hours=3),
        end_time=datetime.now() - timedelta(hours=1),
        enable_evaluation=True,
    )
    meeting_repo.get_by_id.return_value = mock_meeting

    # 1 phiếu Trainer -> Trainee
    trainer_eval = MeetingEvaluation(
        id=1,
        meeting_id=10,
        reviewer_id=1,
        target_user_id=2,
        evaluation_type=EvaluationType.TRAINER_TO_TRAINEE,
        average_score=4.0,
        scores=[
            EvaluationScoreItem(criteria_code="ATTENDANCE_CONDUCT", score=4),
            EvaluationScoreItem(criteria_code="INTERACTION_CONTRIBUTION", score=4),
        ],
    )

    # 1 phiếu Trainee -> Trainer
    trainee_eval = MeetingEvaluation(
        id=2,
        meeting_id=10,
        reviewer_id=2,
        target_user_id=1,
        evaluation_type=EvaluationType.TRAINEE_TO_TRAINER,
        average_score=5.0,
        scores=[
            EvaluationScoreItem(criteria_code="CONTENT_QUALITY", score=5),
            EvaluationScoreItem(criteria_code="TEACHING_METHOD", score=5),
        ],
    )

    eval_repo.get_evaluations_by_meeting.return_value = [trainer_eval, trainee_eval]

    use_case = GetMeetingEvaluationSummaryUseCase(meeting_repo, eval_repo)
    result = await use_case.execute(meeting_id=10)

    assert result.total_evaluations == 2
    assert result.overall_average_score == 4.5
    assert result.total_trainer_evaluations == 1
    assert result.total_trainee_evaluations == 1
    assert result.trainer_average_score == 4.0
    assert result.trainee_average_score == 5.0
    assert len(result.criteria_breakdown) == 4

    # Kiểm tra phân loại evaluation_type trong criteria_breakdown
    trainer_breakdowns = [
        c
        for c in result.criteria_breakdown
        if c.evaluation_type == "TRAINER_TO_TRAINEE"
    ]
    trainee_breakdowns = [
        c
        for c in result.criteria_breakdown
        if c.evaluation_type == "TRAINEE_TO_TRAINER"
    ]
    assert len(trainer_breakdowns) == 2
    assert len(trainee_breakdowns) == 2


@pytest.mark.asyncio
async def test_submit_meeting_overall_evaluation_success():
    from app.meeting.application.get_meeting_overall_evaluation_use_case import (
        GetMeetingOverallEvaluationUseCase,
    )
    from app.meeting.application.submit_meeting_overall_evaluation_use_case import (
        SubmitMeetingOverallEvaluationUseCase,
    )
    from app.meeting.domain.entity import MeetingOverallEvaluation

    meeting_repo = MagicMock()
    overall_repo = MagicMock()

    past_start = datetime.now() - timedelta(hours=3)
    past_end = datetime.now() - timedelta(hours=1)

    mock_meeting = Meeting(
        id=1,
        title="Python 101",
        start_time=past_start,
        end_time=past_end,
        enable_evaluation=True,
        created_by=10,
    )
    meeting_repo.get_by_id.return_value = mock_meeting
    overall_repo.get_by_meeting_id.return_value = None
    overall_repo.exists_for_meeting.return_value = False
    overall_repo.save.side_effect = lambda x: x

    use_case = SubmitMeetingOverallEvaluationUseCase(meeting_repo, overall_repo)
    scores = [
        {"criteria_code": "ATTENDANCE_CONDUCT", "score": 5},
        {"criteria_code": "INTERACTION_CONTRIBUTION", "score": 4},
        {"criteria_code": "ABSORPTION_COMPREHENSION", "score": 5},
        {"criteria_code": "PRE_CLASS_PREPARATION", "score": 4},
    ]

    result = await use_case.execute(
        meeting_id=1,
        trainer_id=10,
        scores_data=scores,
        general_feedback="Lớp học hoàn thành tốt.",
    )

    assert result.meeting_id == 1
    assert result.trainer_id == 10
    assert result.average_score == 4.5
    assert result.general_feedback == "Lớp học hoàn thành tốt."

    # Test GetMeetingOverallEvaluationUseCase
    overall_repo.get_by_meeting_id.return_value = MeetingOverallEvaluation(
        id=1,
        meeting_id=1,
        trainer_id=10,
        average_score=4.5,
        scores=result.scores,
        general_feedback="Lớp học hoàn thành tốt.",
    )
    get_uc = GetMeetingOverallEvaluationUseCase(meeting_repo, overall_repo)
    get_res = await get_uc.execute(meeting_id=1)
    assert get_res.meeting_id == 1
    assert get_res.average_score == 4.5


@pytest.mark.asyncio
async def test_check_evaluation_deadline_creates_violation_when_trainer_missing():
    from app.meeting.application.check_evaluation_deadline_job_use_case import (
        CheckEvaluationDeadlineJobUseCase,
    )

    meeting_repo = MagicMock()
    eval_repo = MagicMock()
    overall_repo = MagicMock()
    violation_repo = MagicMock()

    # Giả lập meeting đã kết thúc > 24h
    orm_meeting = MagicMock()
    orm_meeting.id = 1
    meeting_repo.session.scalars.return_value.all.return_value = [orm_meeting]

    mock_meeting = Meeting(
        id=1,
        title="Python 101",
        start_time=datetime.now() - timedelta(hours=30),
        end_time=datetime.now() - timedelta(hours=28),
        enable_evaluation=True,
        created_by=10,
        participants=[],
    )
    meeting_repo._to_domain.return_value = mock_meeting
    eval_repo.get_evaluations_by_meeting.return_value = []
    overall_repo.exists_for_meeting.return_value = False  # Trainer chưa đánh giá

    # Mock _has_existing_violation
    violation_repo.session.scalars.return_value.first.return_value = None

    job = CheckEvaluationDeadlineJobUseCase(
        meeting_repo, eval_repo, overall_repo, violation_repo
    )
    res = await job.execute()

    assert res["meetings_scanned"] == 1
    assert res["trainer_violations_created"] == 1
    violation_repo.save.assert_called_once()
    saved_violation = violation_repo.save.call_args[0][0]
    assert "Python 101" in saved_violation.reason
    assert mock_meeting.start_time.strftime("%H:%M") in saved_violation.reason
    assert mock_meeting.end_time.strftime("%d/%m/%Y") in saved_violation.reason
