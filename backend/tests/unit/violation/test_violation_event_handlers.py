from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.meeting.domain.events import (
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantStatus
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import PermissionRequestCreated
from app.permission_request.domain.payloads import AbsencePayload, LatePayload
from app.permission_request.domain.value_objects import RequestCategory
from app.violation.application.event_handlers import AutomatedViolationHandler
from app.violation.permission_handler import PermissionViolationHandler


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
        created_by=102,
        note="Bận việc gia đình",
        payload=AbsencePayload(meeting_id=1),
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
        created_by=104,
        note="Kẹt xe",
        payload=LatePayload(
            meeting_id=1,
            start_time=datetime(2026, 9, 25, 14, 30, tzinfo=UTC),
        ),
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
async def test_handle_homework_overdue_creates_violation():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    participant_repo = MagicMock()

    handler = AutomatedViolationHandler(
        create_violation_use_case=create_violation_uc,
        permission_repo=permission_repo,
        participant_repo=participant_repo,
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


@pytest.mark.asyncio
async def test_handle_meeting_absence_skips_violation_when_participant_not_found():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    permission_repo.get_requests_for_meetings.return_value = []
    participant_repo = MagicMock()
    participant_repo.update_participant_status.side_effect = ValueError(
        "Không tìm thấy tham gia của user 105 trong meeting 1"
    )

    handler = AutomatedViolationHandler(
        create_violation_use_case=create_violation_uc,
        permission_repo=permission_repo,
        participant_repo=participant_repo,
    )

    event = ParticipantAbsenceRecorded(
        user_id=105,
        meeting_id=1,
        meeting_title="Họp Lab Tuần 1",
        meeting_date="2026-09-25",
    )

    await handler.handle(event)

    # Should NOT create violation because participant was removed / not found
    assert create_violation_uc.execute.call_count == 0


@pytest.mark.asyncio
async def test_permission_violation_handler_skips_when_count_is_one():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    permission_repo.count_by_user_category_month.return_value = 1

    handler = PermissionViolationHandler(
        create_violation_uc=create_violation_uc,
        permission_repo=permission_repo,
    )

    event = PermissionRequestCreated(
        request_id=1,
        user_id=10,
        category=RequestCategory.ABSENCE,
        note="Xin vắng lần 1",
    )

    await handler.handle(event)

    permission_repo.count_by_user_category_month.assert_called_once()
    assert create_violation_uc.execute.call_count == 0


@pytest.mark.asyncio
async def test_permission_violation_handler_creates_violation_when_exceeding_threshold():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    permission_repo.count_by_user_category_month.return_value = 2

    handler = PermissionViolationHandler(
        create_violation_uc=create_violation_uc,
        permission_repo=permission_repo,
    )

    event = PermissionRequestCreated(
        request_id=2,
        user_id=10,
        category=RequestCategory.ABSENCE,
        note="Xin vắng lần 2",
    )

    await handler.handle(event)

    assert create_violation_uc.execute.call_count == 1
    call_args = create_violation_uc.execute.call_args[1]
    assert call_args["user_ids"] == [10]
    assert "Xin vắng sinh hoạt lần 2 trong tháng" in call_args["reason"]
    assert call_args["is_system"] is True


@pytest.mark.asyncio
async def test_permission_violation_handler_creates_violation_for_postpone():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()
    permission_repo.count_by_user_category_month.return_value = 3

    handler = PermissionViolationHandler(
        create_violation_uc=create_violation_uc,
        permission_repo=permission_repo,
    )

    event = PermissionRequestCreated(
        request_id=3,
        user_id=15,
        category=RequestCategory.POSTPONE,
        note="Xin hoãn lần 3",
        start_time=datetime(2026, 11, 5, 12, 0, tzinfo=UTC),
    )

    await handler.handle(event)

    assert create_violation_uc.execute.call_count == 1
    call_args = create_violation_uc.execute.call_args[1]
    assert call_args["user_ids"] == [15]
    assert "Xin tạm hoãn bài tập lần 3 trong tháng 11/2026" in call_args["reason"]


@pytest.mark.asyncio
async def test_permission_violation_handler_skips_unsupported_category():
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock()
    permission_repo = MagicMock()

    handler = PermissionViolationHandler(
        create_violation_uc=create_violation_uc,
        permission_repo=permission_repo,
    )

    event = PermissionRequestCreated(
        request_id=4,
        user_id=10,
        category=RequestCategory.LATE,
        note="Đi trễ",
    )

    await handler.handle(event)

    permission_repo.count_by_user_category_month.assert_not_called()
    assert create_violation_uc.execute.call_count == 0
