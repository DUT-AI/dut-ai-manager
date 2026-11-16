"""Unit tests for violation occurrence dates (UTC timezone-aware)."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.duty.application.check_overdue_duties_use_case import CheckOverdueDutiesUseCase
from app.duty.domain.entity import CleaningDuty, DutyStatus
from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.meeting.application.check_evaluation_deadline_job_use_case import (
    CheckEvaluationDeadlineJobUseCase,
)
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import (
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantRole, ParticipantStatus
from app.permission_request.domain.events import PermissionRequestCreated
from app.permission_request.domain.value_objects import RequestCategory
from app.violation.application.event_handlers import AutomatedViolationHandler
from app.violation.permission_handler import PermissionViolationHandler


@pytest.mark.asyncio
async def test_meeting_absence_uses_start_time_as_occurrence_date():
    mock_create_uc = AsyncMock()
    mock_perm_repo = MagicMock()
    mock_perm_repo.get_requests_for_meetings.return_value = []
    mock_participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=mock_create_uc,
        permission_repo=mock_perm_repo,
        participant_repo=mock_participant_repo,
    )

    event_start = datetime(2026, 11, 10, 11, 0, tzinfo=UTC)
    event = ParticipantAbsenceRecorded(
        user_id=1,
        meeting_id=10,
        meeting_title="Buổi sinh hoạt tuần 1",
        meeting_date="2026-11-10",
        start_time=event_start,
    )

    await handler.handle(event)

    mock_create_uc.execute.assert_awaited_once()
    kwargs = mock_create_uc.execute.call_args.kwargs
    assert kwargs["date"] == event_start
    assert kwargs["date"].tzinfo is not None
    assert kwargs["date"].tzinfo == UTC
    assert "Vắng sinh hoạt: Buổi sinh hoạt tuần 1 (Không xin phép)" in kwargs["reason"]


@pytest.mark.asyncio
async def test_meeting_late_uses_check_in_at_as_occurrence_date():
    mock_create_uc = AsyncMock()
    mock_perm_repo = MagicMock()
    mock_perm_repo.get_requests_for_meetings.return_value = []
    mock_participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=mock_create_uc,
        permission_repo=mock_perm_repo,
        participant_repo=mock_participant_repo,
    )

    check_in_time = datetime(2026, 11, 10, 11, 25, tzinfo=UTC)
    start_time = datetime(2026, 11, 10, 11, 0, tzinfo=UTC)
    event = ParticipantLateRecorded(
        user_id=2,
        meeting_id=10,
        meeting_title="Buổi sinh hoạt tuần 1",
        check_in_at=check_in_time,
        start_time=start_time,
    )

    await handler.handle(event)

    mock_create_uc.execute.assert_awaited_once()
    kwargs = mock_create_uc.execute.call_args.kwargs
    assert kwargs["date"] == check_in_time
    assert kwargs["date"].tzinfo == UTC
    assert "Đi trễ sinh hoạt: Buổi sinh hoạt tuần 1 (Không xin phép)" in kwargs["reason"]


@pytest.mark.asyncio
async def test_permission_violation_uses_start_time_as_occurrence_date():
    mock_create_uc = AsyncMock()
    mock_perm_repo = MagicMock()
    mock_perm_repo.count_by_user_category_month.return_value = 2

    handler = PermissionViolationHandler(
        create_violation_uc=mock_create_uc,
        permission_repo=mock_perm_repo,
    )

    req_start = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    event = PermissionRequestCreated(
        request_id=100,
        user_id=5,
        category=RequestCategory.ABSENCE,
        note="Xin vắng",
        start_time=req_start,
    )

    await handler.handle(event)

    mock_create_uc.execute.assert_awaited_once()
    kwargs = mock_create_uc.execute.call_args.kwargs
    assert kwargs["date"] == req_start
    assert kwargs["date"].tzinfo == UTC


@pytest.mark.asyncio
async def test_homework_overdue_uses_deadline_as_occurrence_date():
    mock_create_uc = AsyncMock()
    mock_perm_repo = MagicMock()
    mock_participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=mock_create_uc,
        permission_repo=mock_perm_repo,
        participant_repo=mock_participant_repo,
    )

    deadline_utc = datetime(2026, 11, 10, 16, 59, 59, tzinfo=UTC)
    event = HomeworkOverdueDetected(
        user_id=3,
        homework_id=20,
        homework_title="Bài tập Python OOP",
        deadline_date="2026-11-10",
        reason="Chưa hoàn thành bài tập coding (Bài tập Python OOP)",
        deadline=deadline_utc,
    )

    await handler.handle(event)

    mock_create_uc.execute.assert_awaited_once()
    kwargs = mock_create_uc.execute.call_args.kwargs
    assert kwargs["date"] == deadline_utc
    assert kwargs["date"].tzinfo == UTC


@pytest.mark.asyncio
async def test_duty_check_uses_meeting_end_time():
    mock_duty_repo = MagicMock()
    mock_meeting_repo = MagicMock()
    mock_team_repo = MagicMock()
    mock_create_violation_uc = AsyncMock()

    use_case = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_uc,
    )

    meeting_end = datetime(2026, 11, 10, 12, 30, tzinfo=UTC)
    meeting = Meeting(
        id=5,
        title="Buổi học AI",
        start_time=datetime(2026, 11, 10, 11, 0, tzinfo=UTC),
        end_time=meeting_end,
        participants=[
            MeetingParticipant(user_id=7, status=ParticipantStatus.JOINED, check_in_at=datetime(2026, 11, 10, 11, 5, tzinfo=UTC))
        ],
    )
    mock_meeting_repo.get_by_id.return_value = meeting

    duty = CleaningDuty(
        id=1,
        duty_date=date(2026, 11, 10),
        team_id=[1],
        meeting_id=5,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_pending_duties_for_date.return_value = [duty]

    count = await use_case.execute(target_date=date(2026, 11, 10))

    assert count == 1
    mock_create_violation_uc.execute.assert_awaited_once()
    kwargs = mock_create_violation_uc.execute.call_args.kwargs
    assert kwargs["date"] == meeting_end
    assert kwargs["date"].tzinfo == UTC


@pytest.mark.asyncio
async def test_evaluation_deadline_uses_meeting_end_time_plus_24h():
    mock_meeting_repo = MagicMock()
    mock_eval_repo = MagicMock()
    mock_overall_eval_repo = MagicMock()
    mock_violation_repo = MagicMock()

    use_case = CheckEvaluationDeadlineJobUseCase(
        meeting_repo=mock_meeting_repo,
        evaluation_repo=mock_eval_repo,
        overall_eval_repo=mock_overall_eval_repo,
        violation_repo=mock_violation_repo,
    )

    meeting_end = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    meeting = Meeting(
        id=8,
        title="Buổi Seminar",
        start_time=datetime(2026, 11, 10, 10, 0, tzinfo=UTC),
        end_time=meeting_end,
        participants=[
            MeetingParticipant(user_id=9, role=ParticipantRole.TRAINER, status=ParticipantStatus.JOINED),
            MeetingParticipant(user_id=10, role=ParticipantRole.TRAINEE, status=ParticipantStatus.JOINED),
        ],
    )
    mock_meeting_repo.get_meetings_for_evaluation_deadline_check.return_value = [meeting]
    mock_eval_repo.get_evaluations_by_meeting.return_value = []
    mock_overall_eval_repo.exists_for_meeting.return_value = False
    mock_violation_repo.exists_by_user_and_reason.return_value = False

    result = await use_case.execute()

    assert result["trainee_violations_created"] == 1
    assert result["trainer_violations_created"] == 1

    expected_deadline = meeting_end + timedelta(hours=24)
    # Kiểm tra save được gọi với violation mang date == expected_deadline
    saved_violations = [call.args[0] for call in mock_violation_repo.save.call_args_list]
    for v in saved_violations:
        assert v.date == expected_deadline
        assert v.date.tzinfo == UTC
