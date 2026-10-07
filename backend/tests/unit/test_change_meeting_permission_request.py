import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import app.homework.infrastructure.model  # noqa: F401
import app.permission_request.infrastructure.model  # noqa: F401
import app.user.infrastructure.model  # noqa: F401
import app.violation.infrastructure.model  # noqa: F401

from app.core.config import settings
from app.meeting.application.get_upcoming_meetings_with_seats_use_case import (
    GetUpcomingMeetingsWithSeatsUseCase,
)
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.permission_request.application.create_change_meeting_request_use_case import (
    CreateChangeMeetingRequestUseCase,
)
from app.permission_request.application.event_handlers import (
    MeetingParticipantTransferredNotificationHandler,
)
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import (
    MeetingParticipantTransferred,
    PermissionRequestCreated,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.user.domain.entity import UserEntity as User
from app.utils.datetime import get_current_utc7_time



@pytest.mark.asyncio
async def test_change_meeting_success_from_a_to_b():
    permission_repo = MagicMock()
    meeting_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    now = get_current_utc7_time()
    start_b = now + timedelta(days=2)
    end_b = start_b + timedelta(hours=2)

    # Meeting A cũ
    meeting_a = Meeting(
        id=101,
        title="Meeting A (Ca Sáng T7)",
        start_time=now - timedelta(days=1),  # Có thể đã qua
        end_time=now - timedelta(days=1) + timedelta(hours=2),
        participants=[MeetingParticipant(id=1, user_id=10, meeting_id=101)],
    )

    # Meeting B đích
    meeting_b = Meeting(
        id=102,
        title="Meeting B (Ca Chiều CN)",
        start_time=start_b,
        end_time=end_b,
        participants=[MeetingParticipant(id=2, user_id=20, meeting_id=102)],
    )

    meeting_repo.get_meeting_with_lock.return_value = meeting_b
    meeting_repo.get_with_participants.return_value = meeting_a
    permission_repo.get_absence_user_ids_by_meeting.return_value = set()
    def _save_req(req):
        req.id = req.id or 1
        return req
    permission_repo.save.side_effect = _save_req

    use_case = CreateChangeMeetingRequestUseCase(
        permission_repo=permission_repo,
        meeting_repo=meeting_repo,
        event_bus=event_bus,
    )

    result = await use_case.execute(
        note="Xin đổi ca do bận lịch thi",
        meeting_id=102,
        old_meeting_id=101,
        user_id=10,
    )

    # 1. Kiểm tra PermissionRequest trả về
    assert result.category == RequestCategory.CHANGE_MEETING
    assert result.user_id == 10
    assert result.meeting_id == 102
    assert result.old_meeting_id == 101

    # 2. Kiểm tra rút khỏi Meeting A
    assert not any(p.user_id == 10 for p in meeting_a.participants)
    meeting_repo.save.assert_any_call(meeting_a)

    # 3. Kiểm tra thêm vào Meeting B
    assert any(p.user_id == 10 for p in meeting_b.participants)
    meeting_repo.save.assert_any_call(meeting_b)

    # 4. Kiểm tra hủy đơn cũ
    permission_repo.cancel_active_requests_by_meeting.assert_called_once_with(
        user_id=10, meeting_id=101
    )

    # 5. Kiểm tra phát events
    assert event_bus.publish.call_count == 2
    published_types = [call[0][0].__class__ for call in event_bus.publish.call_args_list]
    assert MeetingParticipantTransferred in published_types
    assert PermissionRequestCreated in published_types


@pytest.mark.asyncio
async def test_change_meeting_new_registration_without_old_meeting():
    permission_repo = MagicMock()
    meeting_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    now = get_current_utc7_time()
    meeting_b = Meeting(
        id=102,
        title="Meeting B (Ca Chiều CN)",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=2),
        participants=[],
    )

    meeting_repo.get_meeting_with_lock.return_value = meeting_b
    permission_repo.get_absence_user_ids_by_meeting.return_value = set()
    def _save_req_new(req):
        req.id = req.id or 1
        return req
    permission_repo.save.side_effect = _save_req_new

    use_case = CreateChangeMeetingRequestUseCase(
        permission_repo=permission_repo,
        meeting_repo=meeting_repo,
        event_bus=event_bus,
    )

    result = await use_case.execute(
        note="Học viên mới đăng ký vào ca",
        meeting_id=102,
        old_meeting_id=None,
        user_id=15,
    )

    assert result.category == RequestCategory.CHANGE_MEETING
    assert result.old_meeting_id is None
    assert any(p.user_id == 15 for p in meeting_b.participants)
    permission_repo.cancel_active_requests_by_meeting.assert_not_called()


@pytest.mark.asyncio
async def test_change_meeting_rejects_when_meeting_b_is_full():
    permission_repo = MagicMock()
    meeting_repo = MagicMock()
    event_bus = MagicMock()

    now = get_current_utc7_time()
    # Meeting B có đủ MAX_SEATS = 35 participants
    participants = [
        MeetingParticipant(id=i, user_id=100 + i, meeting_id=103)
        for i in range(settings.MAX_SEATS)
    ]
    meeting_b = Meeting(
        id=103,
        title="Meeting B Full",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=2),
        participants=participants,
    )

    meeting_repo.get_meeting_with_lock.return_value = meeting_b
    permission_repo.get_absence_user_ids_by_meeting.return_value = set()

    use_case = CreateChangeMeetingRequestUseCase(
        permission_repo=permission_repo,
        meeting_repo=meeting_repo,
        event_bus=event_bus,
    )

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            note="Xin vào ca",
            meeting_id=103,
            old_meeting_id=None,
            user_id=999,
        )

    assert exc_info.value.status_code == 400
    assert "hết chỗ ngồi" in exc_info.value.detail


@pytest.mark.asyncio
async def test_change_meeting_considers_absence_requests_as_available_seats():
    permission_repo = MagicMock()
    meeting_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    now = get_current_utc7_time()
    # Meeting B có đủ 35 participants nhưng có 2 người nộp đơn ABSENCE
    participants = [
        MeetingParticipant(id=i, user_id=100 + i, meeting_id=104)
        for i in range(settings.MAX_SEATS)
    ]
    meeting_b = Meeting(
        id=104,
        title="Meeting B with 2 Absences",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=2),
        participants=participants,
    )

    meeting_repo.get_meeting_with_lock.return_value = meeting_b
    # User 100 và 101 có đơn ABSENCE
    permission_repo.get_absence_user_ids_by_meeting.return_value = {100, 101}
    def _save_req_abs(req):
        req.id = req.id or 1
        return req
    permission_repo.save.side_effect = _save_req_abs

    use_case = CreateChangeMeetingRequestUseCase(
        permission_repo=permission_repo,
        meeting_repo=meeting_repo,
        event_bus=event_bus,
    )

    # Đổi thành công vì ghế khả dụng = 35 - (35 - 2) = 2 > 0
    result = await use_case.execute(
        note="Đổi vào ghế của người vắng",
        meeting_id=104,
        old_meeting_id=None,
        user_id=888,
    )

    assert result.category == RequestCategory.CHANGE_MEETING
    assert any(p.user_id == 888 for p in meeting_b.participants)


@pytest.mark.asyncio
async def test_change_meeting_rejects_when_meeting_b_in_past():
    permission_repo = MagicMock()
    meeting_repo = MagicMock()
    event_bus = MagicMock()

    now = get_current_utc7_time()
    meeting_b = Meeting(
        id=105,
        title="Meeting B in Past",
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
        participants=[],
    )

    meeting_repo.get_meeting_with_lock.return_value = meeting_b

    use_case = CreateChangeMeetingRequestUseCase(
        permission_repo=permission_repo,
        meeting_repo=meeting_repo,
        event_bus=event_bus,
    )

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            note="Xin vào ca đã bắt đầu",
            meeting_id=105,
            old_meeting_id=None,
            user_id=10,
        )

    assert exc_info.value.status_code == 400
    assert "đã bắt đầu hoặc đã kết thúc" in exc_info.value.detail


@pytest.mark.asyncio
async def test_change_meeting_rejects_same_meeting_id():
    permission_repo = MagicMock()
    meeting_repo = MagicMock()
    event_bus = MagicMock()

    use_case = CreateChangeMeetingRequestUseCase(
        permission_repo=permission_repo,
        meeting_repo=meeting_repo,
        event_bus=event_bus,
    )

    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute(
            note="Đổi sang chính nó",
            meeting_id=100,
            old_meeting_id=100,
            user_id=10,
        )

    assert exc_info.value.status_code == 400
    assert "Không thể đổi sang cùng một buổi họp" in exc_info.value.detail


def test_get_upcoming_meetings_with_seats():
    meeting_repo = MagicMock()
    permission_repo = MagicMock()

    now = get_current_utc7_time()
    m1 = Meeting(
        id=1,
        title="Meeting 1",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=2),
        participants=[MeetingParticipant(id=1, user_id=11)],
    )
    m2 = Meeting(
        id=2,
        title="Meeting 2",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=2),
        participants=[],
    )

    meeting_repo.get_all_with_participants.return_value = [m1, m2]
    permission_repo.get_absence_user_ids_by_meeting.return_value = set()

    use_case = GetUpcomingMeetingsWithSeatsUseCase(
        meeting_repo=meeting_repo,
        permission_repo=permission_repo,
    )

    results = use_case.execute(from_date=now)

    assert len(results) == 2
    assert results[0].id == 1
    assert results[0].occupied_seats == 1
    assert results[0].available_seats == settings.MAX_SEATS - 1
    assert results[0].is_full is False

    assert results[1].id == 2
    assert results[1].occupied_seats == 0
    assert results[1].available_seats == settings.MAX_SEATS
    assert results[1].is_full is False


@pytest.mark.asyncio
async def test_meeting_participant_transferred_notification_handler():
    notification_service = MagicMock()
    notification_service.send_to_user = AsyncMock()
    notification_service.send_to_room = AsyncMock()

    user_repo = MagicMock()
    user = User(
        id=10,
        name="Nguyễn Văn A",
        email="test@example.com",
        discord_id="discord_123",
        zalo_bot_id="zalo_123",
    )
    user_repo.get_by_id.return_value = user

    meeting_repo = MagicMock()
    now = get_current_utc7_time()
    m_old = Meeting(id=101, title="Ca Cũ", start_time=now, end_time=now + timedelta(hours=2))
    m_new = Meeting(id=102, title="Ca Mới", start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
    meeting_repo.get_by_id.side_effect = lambda mid: m_old if mid == 101 else m_new

    handler = MeetingParticipantTransferredNotificationHandler(
        notification_service=notification_service,
        user_repo=user_repo,
        meeting_repo=meeting_repo,
    )

    event = MeetingParticipantTransferred(
        request_id=1,
        user_id=10,
        old_meeting_id=101,
        new_meeting_id=102,
        note="Bận việc",
    )

    await handler.handle(event)
    await asyncio.sleep(0.01)  # Chờ create_task chạy

    assert notification_service.send_to_user.call_count == 1
    assert notification_service.send_to_room.call_count == 1
