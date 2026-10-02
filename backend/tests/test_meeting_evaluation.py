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
