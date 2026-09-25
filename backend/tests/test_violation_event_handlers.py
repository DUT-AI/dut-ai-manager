import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.meeting.domain.events import (
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantStatus
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.value_objects import RequestCategory
from app.violation.application.event_handlers import AutomatedViolationHandler


@pytest.mark.asyncio
async def test_handle_meeting_absence_without_permission_creates_violation():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    permission_repo.get_requests_for_meetings.return_value = []
    participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=create_violation_uc,
        permission_repo=permission_repo,
        participant_repo=participant_repo,
    )

    event = ParticipantAbsenceRecorded(
        user_id=101,
        meeting_id=1,
        meeting_title="Họp Lab Tuần 1",
        meeting_date="2026-09-25",
    )

    await handler.handle(event)

    # Should create violation
    assert create_violation_uc.execute.call_count == 1
    call_args = create_violation_uc.execute.call_args[1]
    assert call_args["user_ids"] == [101]
    assert "Vắng sinh hoạt: Họp Lab Tuần 1 (Không xin phép)" in call_args["reason"]
    assert call_args["is_system"] is True

    # Should update participant status to ABSENT_UNEXCUSED
    participant_repo.update_participant_status.assert_called_once_with(
        meeting_id=1,
        user_id=101,
        status=ParticipantStatus.ABSENT_UNEXCUSED,
    )


@pytest.mark.asyncio
async def test_handle_meeting_absence_with_permission_skips_violation():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    
    excused_req = PermissionRequest(
        id=1,
        user_id=102,
        category=RequestCategory.ABSENCE,
        note="Bận việc gia đình",
        meeting_id=1,
    )
    permission_repo.get_requests_for_meetings.return_value = [excused_req]
    participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=create_violation_uc,
        permission_repo=permission_repo,
        participant_repo=participant_repo,
    )

    event = ParticipantAbsenceRecorded(
        user_id=102,
        meeting_id=1,
        meeting_title="Họp Lab Tuần 1",
        meeting_date="2026-09-25",
    )

    await handler.handle(event)

    # Should NOT create violation
    assert create_violation_uc.execute.call_count == 0

    # Should update participant status to ABSENT_EXCUSED
    participant_repo.update_participant_status.assert_called_once_with(
        meeting_id=1,
        user_id=102,
        status=ParticipantStatus.ABSENT_EXCUSED,
    )


@pytest.mark.asyncio
async def test_handle_meeting_late_without_permission_creates_violation():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    permission_repo.get_requests_for_meetings.return_value = []
    participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=create_violation_uc,
        permission_repo=permission_repo,
        participant_repo=participant_repo,
    )

    event = ParticipantLateRecorded(
        user_id=103,
        meeting_id=1,
        meeting_title="Họp Lab Tuần 1",
        check_in_at=datetime(2026, 9, 25, 14, 20),
        start_time=datetime(2026, 9, 25, 14, 0),
    )

    await handler.handle(event)

    # Should create violation
    assert create_violation_uc.execute.call_count == 1
    call_args = create_violation_uc.execute.call_args[1]
    assert call_args["user_ids"] == [103]
    assert "Đi trễ sinh hoạt: Họp Lab Tuần 1 (Không xin phép)" in call_args["reason"]

    # Should update participant status to LATE_UNEXCUSED
    participant_repo.update_participant_status.assert_called_once_with(
        meeting_id=1,
        user_id=103,
        status=ParticipantStatus.LATE_UNEXCUSED,
    )


@pytest.mark.asyncio
async def test_handle_meeting_late_with_valid_permission_skips_violation():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()

    late_req = PermissionRequest(
        id=2,
        user_id=104,
        category=RequestCategory.LATE,
        note="Kẹt xe",
        meeting_id=1,
        start_time=datetime(2026, 9, 25, 14, 30),
    )
    permission_repo.get_requests_for_meetings.return_value = [late_req]
    participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=create_violation_uc,
        permission_repo=permission_repo,
        participant_repo=participant_repo,
    )

    # Arrived at 14:20 (before 14:30 permitted)
    event = ParticipantLateRecorded(
        user_id=104,
        meeting_id=1,
        meeting_title="Họp Lab Tuần 1",
        check_in_at=datetime(2026, 9, 25, 14, 20),
        start_time=datetime(2026, 9, 25, 14, 0),
    )

    await handler.handle(event)

    # Should NOT create violation
    assert create_violation_uc.execute.call_count == 0

    # Should update participant status to LATE_EXCUSED
    participant_repo.update_participant_status.assert_called_once_with(
        meeting_id=1,
        user_id=104,
        status=ParticipantStatus.LATE_EXCUSED,
    )


@pytest.mark.asyncio
async def test_handle_homework_overdue_without_postpone_creates_violation():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    permission_repo.get_postpone_requests_for_homeworks.return_value = []

    handler = AutomatedViolationHandler(
        create_violation_use_case=create_violation_uc,
        permission_repo=permission_repo,
    )

    event = HomeworkOverdueDetected(
        user_id=201,
        homework_id=5,
        homework_title="Bài tập Pytest",
        deadline_date="2026-09-25",
        reason="Chưa hoàn thành bài tập coding (Bài tập Pytest)",
    )

    await handler.handle(event)

    assert create_violation_uc.execute.call_count == 1
    call_args = create_violation_uc.execute.call_args[1]
    assert call_args["user_ids"] == [201]
    assert "Chưa hoàn thành bài tập coding (Bài tập Pytest)" in call_args["reason"]
