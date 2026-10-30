from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.permission_request.application.create_permission_request_use_case import (
    CreatePermissionRequestUseCase,
)
from app.permission_request.application.strategies import (
    LateStrategy,
    PermissionStrategyRegistry,
)
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import LatePayload
from app.permission_request.domain.value_objects import RequestCategory


def test_permission_request_validate_late_success():
    """Kiểm tra đơn xin đi trễ hợp lệ qua LateStrategy."""
    meeting_repo = MagicMock()
    meeting = Meeting(
        title="Buổi sinh hoạt AI",
        start_time=datetime(2026, 10, 31, 8, 30, tzinfo=UTC),
        end_time=datetime(2026, 10, 31, 11, 0, tzinfo=UTC),
    )
    meeting_repo.get_by_id.return_value = meeting
    permission_repo = MagicMock()
    strategy = LateStrategy(permission_repo=permission_repo, meeting_repo=meeting_repo)

    req = PermissionRequest(
        user_id=1,
        note="Kẹt xe đến trễ 30 phút",
        payload=LatePayload(
            meeting_id=10,
            start_time=datetime(2026, 10, 31, 9, 0, tzinfo=UTC),
        ),
    )

    # Không raise exception
    strategy.validate(req)


def test_permission_request_validate_late_meeting_ended():
    """Không thể xin trễ cho meeting đã kết thúc."""
    now = datetime(2026, 10, 31, 11, 30, tzinfo=UTC)
    meeting_repo = MagicMock()
    meeting = Meeting(
        title="Buổi sinh hoạt AI",
        start_time=datetime(2026, 10, 31, 8, 30, tzinfo=UTC),
        end_time=datetime(2026, 10, 31, 11, 0, tzinfo=UTC),
    )
    meeting_repo.get_by_id.return_value = meeting
    permission_repo = MagicMock()
    strategy = LateStrategy(permission_repo=permission_repo, meeting_repo=meeting_repo)

    req = PermissionRequest(
        user_id=1,
        note="Đi trễ",
        payload=LatePayload(
            meeting_id=10,
            start_time=datetime(2026, 10, 31, 9, 0, tzinfo=UTC),
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req, now=now)
    assert exc_info.value.status_code == 400
    assert (
        "Không thể xin đi trễ cho buổi sinh hoạt đã kết thúc" in exc_info.value.detail
    )


def test_permission_request_validate_late_before_meeting_start():
    """Giờ đến dự kiến không được trước khi meeting bắt đầu."""
    meeting_repo = MagicMock()
    meeting = Meeting(
        title="Buổi sinh hoạt AI",
        start_time=datetime(2026, 10, 31, 8, 30, tzinfo=UTC),
        end_time=datetime(2026, 10, 31, 11, 0, tzinfo=UTC),
    )
    meeting_repo.get_by_id.return_value = meeting
    permission_repo = MagicMock()
    strategy = LateStrategy(permission_repo=permission_repo, meeting_repo=meeting_repo)

    req = PermissionRequest(
        user_id=1,
        note="Đi trễ",
        payload=LatePayload(
            meeting_id=10,
            start_time=datetime(2026, 10, 31, 8, 15, tzinfo=UTC),
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req)
    assert exc_info.value.status_code == 400
    assert "Thời gian dự kiến đến phải sau giờ bắt đầu" in exc_info.value.detail


def test_permission_request_validate_late_after_meeting_end():
    """Giờ đến dự kiến không được sau khi meeting đã kết thúc."""
    meeting_repo = MagicMock()
    meeting = Meeting(
        title="Buổi sinh hoạt AI",
        start_time=datetime(2026, 10, 31, 8, 30, tzinfo=UTC),
        end_time=datetime(2026, 10, 31, 11, 0, tzinfo=UTC),
    )
    meeting_repo.get_by_id.return_value = meeting
    permission_repo = MagicMock()
    strategy = LateStrategy(permission_repo=permission_repo, meeting_repo=meeting_repo)

    req = PermissionRequest(
        user_id=1,
        note="Đi trễ",
        payload=LatePayload(
            meeting_id=10,
            start_time=datetime(2026, 10, 31, 11, 15, tzinfo=UTC),
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req)
    assert exc_info.value.status_code == 400
    assert (
        "Thời gian dự kiến đến không được vượt quá lúc kết thúc buổi họp"
        in exc_info.value.detail
    )


def test_participant_check_in_on_time_with_late_permission():
    """Học viên có đơn xin trễ nhưng thực tế đến đúng giờ -> Trạng thái là JOINED."""
    participant = MeetingParticipant(
        user_id=1,
        meeting_id=10,
        status=ParticipantStatus.LATE_EXCUSED,
    )
    meeting_start = datetime(2026, 10, 31, 8, 30, tzinfo=UTC)
    check_in_time = datetime(2026, 10, 31, 8, 25, tzinfo=UTC)

    success, msg, is_late = participant.record_check_in(
        check_in_time=check_in_time,
        meeting_start_time=meeting_start,
    )

    assert success is True
    assert is_late is False
    assert participant.status == ParticipantStatus.JOINED


def test_participant_check_in_late_with_late_permission():
    """Học viên có đơn xin trễ và đến trễ -> Bảo lưu LATE_EXCUSED."""
    participant = MeetingParticipant(
        user_id=1,
        meeting_id=10,
        status=ParticipantStatus.LATE_EXCUSED,
    )
    meeting_start = datetime(2026, 10, 31, 8, 30, tzinfo=UTC)
    check_in_time = datetime(2026, 10, 31, 8, 45, tzinfo=UTC)

    success, msg, is_late = participant.record_check_in(
        check_in_time=check_in_time,
        meeting_start_time=meeting_start,
    )

    assert success is True
    assert is_late is True
    assert participant.status == ParticipantStatus.LATE_EXCUSED


@pytest.mark.asyncio
async def test_create_permission_request_use_case_late_updates_participant():
    """Use case tạo đơn LATE hợp lệ cập nhật participant sang LATE_EXCUSED."""
    from unittest.mock import AsyncMock

    repo = MagicMock()
    meeting_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    meeting = Meeting(
        title="Họp Team",
        start_time=datetime(2026, 10, 31, 8, 30, tzinfo=UTC),
        end_time=datetime(2026, 10, 31, 11, 0, tzinfo=UTC),
    )

    def mock_save(req):
        req.id = 99
        return req

    meeting_repo.get_by_id.return_value = meeting
    repo.save.side_effect = mock_save

    strategy = LateStrategy(permission_repo=repo, meeting_repo=meeting_repo)
    strategy_registry = PermissionStrategyRegistry([strategy])

    uc = CreatePermissionRequestUseCase(
        repo=repo,
        strategy_registry=strategy_registry,
        event_bus=event_bus,
    )

    result = await uc.execute(
        category=RequestCategory.LATE,
        note="Đến muộn 20p",
        meeting_id=5,
        start_time=datetime(2026, 10, 31, 8, 50, tzinfo=UTC),
        user_id=12,
    )

    assert result.category == RequestCategory.LATE
    repo.mark_participant_late_excused.assert_called_once_with(5, 12)
