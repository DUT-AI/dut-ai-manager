"""
Unit tests for Duty Use Cases.
"""

from datetime import date, datetime, time, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.duty.application.check_overdue_duties_use_case import (
    CheckOverdueDutiesUseCase,
)
from app.duty.application.dtos import UpdateDutyRequest
from app.duty.application.get_duties_use_case import GetDutiesUseCase
from app.duty.application.manage_duty_use_case import (
    DeleteDutyUseCase,
    RestoreDutyUseCase,
    UpdateDutyUseCase,
)
from app.duty.application.submit_duty_evidence_use_case import (
    SubmitDutyEvidenceUseCase,
)
from app.duty.application.toggle_duty_schedule_use_case import (
    BatchCreateDutyUseCase,
    ToggleDutyScheduleUseCase,
)
from app.duty.domain.entity import CleaningDuty, DutyStatus
from app.duty.domain.events import (
    DutyScheduled,
    DutySubmitted,
    DutyUpdated,
)
from app.duty.notification_handler import DutyNotificationHandler
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import MeetingUpdated
from app.meeting.domain.value_objects import ParticipantStatus
from app.shared.application.response import BadRequestException
from app.violation.domain.events import ViolationCreated
from app.violation.notification_handler import ViolationNotificationHandler


@pytest.fixture
def mock_duty_repo():
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_team_repo():
    repo = MagicMock()
    mock_team = MagicMock()
    mock_team.id = 12
    mock_team.team_name = "Gen 2 - thứ 3 - 17h30 - 19h30"
    mock_team.member_ids = [101, 102, 103]
    repo.get_by_id.return_value = mock_team
    return repo


@pytest.fixture
def mock_meeting_repo():
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    mock_user = MagicMock()
    mock_user.id = 101
    mock_user.name = "Trần Thị Tuyết Trinh"
    repo.get_by_id.return_value = mock_user
    return repo


@pytest.fixture
def mock_notification_service():
    from app.shared.infrastructure.notification.channel import (
        ChannelDeliveryResult,
        ChannelType,
    )

    service = MagicMock()
    service.dispatch = AsyncMock(return_value={})
    service.dispatch_room = AsyncMock(
        return_value=ChannelDeliveryResult(
            channel=ChannelType.DISCORD, success=True, status="SENT"
        )
    )
    service.send_to_room = service.dispatch_room
    service.send_to_user = service.dispatch
    return service


@pytest.fixture
def mock_minio_service():
    service = MagicMock()
    service.upload_file = AsyncMock(return_value="https://minio.dut.vn/duty-proof.jpg")
    return service


@pytest.fixture
def mock_create_violation_use_case():
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=[])
    return uc


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.mark.asyncio
async def test_toggle_duty_schedule_enable(
    mock_duty_repo, mock_meeting_repo, mock_team_repo, mock_event_bus
):
    """Test bật lịch trực nhật cho nhóm Gen 2 khi có meeting."""
    mock_duty_repo.get_by_date_and_team.return_value = None
    mock_meeting = MagicMock()
    mock_meeting.id = 100
    mock_meeting_repo.get_by_date.return_value = [mock_meeting]

    saved_duty = CleaningDuty(
        id=1,
        duty_date=date(2026, 10, 20),
        team_id=12,
        team_name="Gen 2 - thứ 3 - 17h30 - 19h30",
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.save.return_value = saved_duty

    uc = ToggleDutyScheduleUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        event_bus=mock_event_bus,
    )

    result = await uc.execute(duty_date=date(2026, 10, 20), team_id=12, enabled=True)

    assert result is not None
    assert result.team_id == [12]
    assert result.status == DutyStatus.PENDING.value
    mock_duty_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_toggle_duty_schedule_enable_without_meeting(
    mock_duty_repo, mock_meeting_repo, mock_team_repo, mock_event_bus
):
    """Test bật ca trực tự do thành công ngay cả khi không có lịch meeting."""
    mock_duty_repo.get_by_date_and_team.return_value = None
    mock_meeting_repo.get_by_date.return_value = []

    saved_duty = CleaningDuty(
        id=2,
        duty_date=date(2026, 10, 20),
        team_id=[12],
        team_name="Gen 2 - thứ 3 - 17h30 - 19h30",
        meeting_id=None,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.save.return_value = saved_duty

    uc = ToggleDutyScheduleUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        event_bus=mock_event_bus,
    )

    result = await uc.execute(duty_date=date(2026, 10, 20), team_id=12, enabled=True)
    assert result is not None
    assert result.team_id == [12]
    assert result.meeting_id is None
    assert result.status == DutyStatus.PENDING.value
    mock_duty_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_toggle_duty_schedule_disable(
    mock_duty_repo, mock_meeting_repo, mock_team_repo
):
    """Test tắt ca trực nhật theo Meeting: chuyển sang CANCELLED để giữ lại trên giao diện Lịch Tuần với Switch OFF."""
    existing_duty = CleaningDuty(
        id=1,
        duty_date=date(2026, 10, 20),
        team_id=12,
        meeting_id=100,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_date_and_team.return_value = existing_duty

    uc = ToggleDutyScheduleUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        event_bus=MagicMock(),
    )

    result = await uc.execute(duty_date=date(2026, 10, 20), team_id=12, enabled=False)

    assert result is None
    assert existing_duty.status == DutyStatus.CANCELLED
    mock_duty_repo.save.assert_called_once_with(existing_duty)


@pytest.mark.asyncio
async def test_toggle_duty_schedule_disable_free_duty(
    mock_duty_repo, mock_meeting_repo, mock_team_repo
):
    """Test tắt ca trực tự do: chuyển sang CANCELLED chứ không xóa khỏi hệ thống."""
    existing_duty = CleaningDuty(
        id=2,
        duty_date=date(2026, 10, 20),
        team_id=12,
        meeting_id=None,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_date_and_team.return_value = existing_duty

    uc = ToggleDutyScheduleUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        event_bus=MagicMock(),
    )

    result = await uc.execute(duty_date=date(2026, 10, 20), team_id=12, enabled=False)

    assert result is None
    assert existing_duty.status == DutyStatus.CANCELLED
    mock_duty_repo.save.assert_called_once_with(existing_duty)


@pytest.mark.asyncio
async def test_submit_duty_evidence_success(
    mock_duty_repo, mock_team_repo, mock_minio_service, mock_event_bus
):
    """Test 1 người đại diện nộp ảnh và checklist >= 1 -> COMPLETED."""
    duty = CleaningDuty(
        id=1,
        duty_date=date.today(),
        team_id=12,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_id.return_value = duty
    mock_duty_repo.save.side_effect = lambda d: d

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "clean_lab.jpg"
    mock_file.content_type = "image/jpeg"
    mock_file.read = AsyncMock(return_value=b"fake-image-bytes")

    uc = SubmitDutyEvidenceUseCase(
        duty_repo=mock_duty_repo,
        team_repo=mock_team_repo,
        minio_service=mock_minio_service,
        event_bus=mock_event_bus,
    )

    result = await uc.execute(
        duty_id=1,
        user_id=101,  # In team member_ids
        files=[mock_file],
        checklist=[
            {"id": "floor", "title": "Lau sàn", "checked": True},
            {"id": "tables", "title": "Lau bàn", "checked": True},
        ],
        note="Đã quét sàn và lau bàn",
        is_admin=True,
    )

    assert result.status == DutyStatus.AWAITING_APPROVAL.value
    assert any(
        item["title"] == "Lau sàn" and item["checked"] for item in result.checklist
    )
    assert result.note == "Đã quét sàn và lau bàn"
    assert len(result.evidence_image_urls) == 1


@pytest.mark.asyncio
async def test_approve_duty_by_admin(mock_duty_repo, mock_event_bus):
    """Test Admin/HR duyệt ca trực -> Chuyển thành COMPLETED."""
    from app.duty.application.review_duty_use_case import ApproveDutyUseCase

    duty = CleaningDuty(
        id=1,
        duty_date=date.today(),
        team_id=12,
        status=DutyStatus.AWAITING_APPROVAL,
    )
    mock_duty_repo.get_by_id.return_value = duty
    mock_duty_repo.save.side_effect = lambda d: d

    uc = ApproveDutyUseCase(duty_repo=mock_duty_repo, event_bus=mock_event_bus)
    result = await uc.execute(duty_id=1, admin_id=999)

    assert result.status == DutyStatus.COMPLETED.value
    assert result.approved_by == 999


@pytest.mark.asyncio
async def test_reject_duty_by_admin(mock_duty_repo, mock_event_bus):
    """Test Admin/HR từ chối ca trực -> Chuyển thành REJECTED kèm lý do."""
    from app.duty.application.review_duty_use_case import RejectDutyUseCase

    duty = CleaningDuty(
        id=1,
        duty_date=date.today(),
        team_id=12,
        status=DutyStatus.AWAITING_APPROVAL,
    )
    mock_duty_repo.get_by_id.return_value = duty
    mock_duty_repo.save.side_effect = lambda d: d

    uc = RejectDutyUseCase(duty_repo=mock_duty_repo, event_bus=mock_event_bus)
    result = await uc.execute(
        duty_id=1, admin_id=999, reason="Sàn còn bẩn, chưa lau bàn"
    )

    assert result.status == DutyStatus.REJECTED.value
    assert result.rejection_reason == "Sàn còn bẩn, chưa lau bàn"
    assert result.rejected_by == 999


@pytest.mark.asyncio
async def test_check_overdue_duties_penalizes_only_checked_in_users(
    mock_duty_repo,
    mock_meeting_repo,
    mock_team_repo,
    mock_create_violation_use_case,
    mock_event_bus,
):
    """
    Test lúc 23:59: Buổi học có 3 học viên, nhưng chỉ 2 người check-in.
    Nếu ca trực chưa nộp ảnh -> CHỈ PHẠT 2 NGƯỜI ĐÃ CHECK-IN.
    """
    target_date = date.today()

    duty = CleaningDuty(
        id=1,
        duty_date=target_date,
        team_id=12,
        meeting_id=99,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_pending_duties_for_date.return_value = [duty]

    # Meeting có 3 participants: 101 (check-in), 102 (check-in), 103 (chưa check-in / vắng)
    meeting = Meeting(
        id=99,
        title="Buổi học AI",
        start_time=datetime(2026, 10, 19, 17, 30),
        end_time=datetime(2026, 10, 19, 19, 30),
        participants=[
            MeetingParticipant(user_id=101, check_in_at=datetime(2026, 10, 19, 17, 25)),
            MeetingParticipant(user_id=102, check_in_at=datetime(2026, 10, 19, 17, 35)),
            MeetingParticipant(user_id=103, check_in_at=None),  # Vắng mặt
        ],
    )
    mock_meeting_repo.get_by_id.return_value = meeting

    uc = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_use_case,
        event_bus=mock_event_bus,
    )

    violations_count = await uc.execute(target_date=target_date)

    # Chỉ phạt 2 người (101 và 102)
    assert violations_count == 2
    mock_create_violation_use_case.execute.assert_called_once()
    called_kwargs = mock_create_violation_use_case.execute.call_args.kwargs
    assert set(called_kwargs["user_ids"]) == {101, 102}
    assert 103 not in called_kwargs["user_ids"]

    assert duty.status == DutyStatus.VIOLATED


@pytest.mark.asyncio
async def test_check_overdue_duties_skips_when_completed(
    mock_duty_repo, mock_meeting_repo, mock_team_repo, mock_create_violation_use_case
):
    """Ca trực đã COMPLETED thì không quét vi phạm."""
    mock_duty_repo.get_pending_duties_for_date.return_value = []

    uc = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_use_case,
        event_bus=MagicMock(),
    )

    violations_count = await uc.execute(target_date=date.today())
    assert violations_count == 0
    mock_create_violation_use_case.execute.assert_not_called()


@pytest.mark.asyncio
async def test_toggle_duty_schedule_disable_completed_raises_error(
    mock_duty_repo, mock_meeting_repo, mock_team_repo
):
    """Không cho phép tắt Switch hủy ca trực khi đã COMPLETED."""
    existing_duty = CleaningDuty(
        id=1,
        duty_date=date(2026, 10, 20),
        team_id=12,
        status=DutyStatus.COMPLETED,
    )
    mock_duty_repo.get_by_date_and_team.return_value = existing_duty

    uc = ToggleDutyScheduleUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        event_bus=MagicMock(),
    )

    with pytest.raises(BadRequestException) as exc_info:
        await uc.execute(duty_date=date(2026, 10, 20), team_id=12, enabled=False)

    assert "đã hoàn thành nghiệm thu" in exc_info.value.message
    mock_duty_repo.delete.assert_not_called()


@pytest.mark.asyncio
async def test_toggle_duty_schedule_disable_awaiting_approval_raises_error(
    mock_duty_repo, mock_meeting_repo, mock_team_repo
):
    """Không cho phép tắt Switch hủy ca trực khi đang AWAITING_APPROVAL."""
    existing_duty = CleaningDuty(
        id=1,
        duty_date=date(2026, 10, 20),
        team_id=12,
        status=DutyStatus.AWAITING_APPROVAL,
    )
    mock_duty_repo.get_by_date_and_team.return_value = existing_duty

    uc = ToggleDutyScheduleUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        event_bus=MagicMock(),
    )

    with pytest.raises(BadRequestException) as exc_info:
        await uc.execute(duty_date=date(2026, 10, 20), team_id=12, enabled=False)

    assert "đang chờ Admin/HR duyệt" in exc_info.value.message
    mock_duty_repo.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_duty_completed_raises_error(mock_duty_repo):
    """Không cho phép xóa ca trực khi đã COMPLETED."""
    duty = CleaningDuty(
        id=10,
        duty_date=date(2026, 10, 20),
        team_id=12,
        status=DutyStatus.COMPLETED,
    )
    mock_duty_repo.get_by_id.return_value = duty

    uc = DeleteDutyUseCase(duty_repo=mock_duty_repo)

    with pytest.raises(BadRequestException) as exc_info:
        await uc.execute(duty_id=10)

    assert "đã hoàn thành nghiệm thu" in exc_info.value.message
    mock_duty_repo.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_duty_awaiting_approval_raises_error(mock_duty_repo):
    """Không cho phép xóa ca trực khi đang AWAITING_APPROVAL."""
    duty = CleaningDuty(
        id=11,
        duty_date=date(2026, 10, 20),
        team_id=12,
        status=DutyStatus.AWAITING_APPROVAL,
    )
    mock_duty_repo.get_by_id.return_value = duty

    uc = DeleteDutyUseCase(duty_repo=mock_duty_repo)

    with pytest.raises(BadRequestException) as exc_info:
        await uc.execute(duty_id=11)

    assert "đang chờ Admin/HR duyệt" in exc_info.value.message
    mock_duty_repo.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_duty_success_sets_cancelled(mock_duty_repo):
    """Test xóa ca trực nhật: chuyển sang CANCELLED để lưu vào lịch sử."""
    duty = CleaningDuty(
        id=12,
        duty_date=date(2026, 10, 20),
        team_id=12,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_id.return_value = duty

    uc = DeleteDutyUseCase(duty_repo=mock_duty_repo)
    success = await uc.execute(duty_id=12)

    assert success is True
    assert duty.status == DutyStatus.CANCELLED
    mock_duty_repo.save.assert_called_once_with(duty)


@pytest.mark.asyncio
async def test_restore_duty_success(mock_duty_repo):
    """Test hồi phục ca trực nhật từ CANCELLED về PENDING."""
    duty = CleaningDuty(
        id=13,
        duty_date=date(2026, 10, 20),
        team_id=12,
        status=DutyStatus.CANCELLED,
    )
    mock_duty_repo.get_by_id.return_value = duty
    mock_duty_repo.save.return_value = duty

    uc = RestoreDutyUseCase(duty_repo=mock_duty_repo)
    result = await uc.execute(duty_id=13)

    assert result is not None
    assert duty.status == DutyStatus.PENDING
    assert result.status == DutyStatus.PENDING.value
    mock_duty_repo.save.assert_called_once_with(duty)


@pytest.mark.asyncio
async def test_check_overdue_duties_includes_transferred_students_and_excludes_trainers(
    mock_duty_repo,
    mock_meeting_repo,
    mock_team_repo,
    mock_create_violation_use_case,
    mock_event_bus,
):
    """
    Test xử lý đúng đối tượng tham gia Meeting:
    - Trong meeting có:
      + Trainer/Creator: user_id=999 (created_by của meeting) -> KHÔNG ĐƯỢC PHẠT
      + Học viên nhóm khác đổi lớp sang học: user_id=888 (đã check-in tham gia buổi học) -> VẪN TÍNH VÀ BỊ PHẠT
      + Học viên nhóm trực có mặt: user_id=101, user_id=102 (đã check-in) -> BỊ PHẠT
      + Học viên nhóm trực vắng mặt: user_id=103 (chưa check-in / check_in_at=None) -> KHÔNG ĐƯỢC PHẠT
      + Học viên nhóm trực vắng có phép: user_id=104 (status=ABSENT_EXCUSED) -> KHÔNG ĐƯỢC PHẠT
      => Tổng số bị phạt là 3: {101, 102, 888}. Loại trừ Trainer (999) và học viên vắng (103, 104).
    """
    target_date = date.today()
    duty = CleaningDuty(
        id=5,
        duty_date=target_date,
        team_id=12,
        meeting_id=100,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_pending_duties_for_date.return_value = [duty]

    meeting = Meeting(
        id=100,
        title="Buổi học Fullstack",
        start_time=datetime(2026, 10, 19, 17, 30),
        end_time=datetime(2026, 10, 19, 19, 30),
        participants=[
            MeetingParticipant(
                user_id=999, check_in_at=datetime(2026, 10, 19, 17, 20)
            ),  # Trainer
            MeetingParticipant(
                user_id=888, check_in_at=datetime(2026, 10, 19, 17, 25)
            ),  # Học viên nhóm khác đổi lớp
            MeetingParticipant(
                user_id=101, check_in_at=datetime(2026, 10, 19, 17, 28)
            ),  # Nhóm trực - có mặt
            MeetingParticipant(
                user_id=102, check_in_at=datetime(2026, 10, 19, 17, 29)
            ),  # Nhóm trực - có mặt
            MeetingParticipant(user_id=103, check_in_at=None),  # Nhóm trực - vắng mặt
            MeetingParticipant(
                user_id=104,
                check_in_at=None,
                status=ParticipantStatus.ABSENT_EXCUSED,
            ),
        ],
    )
    meeting.created_by = 999  # Trainer là creator
    mock_meeting_repo.get_by_id.return_value = meeting

    uc = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_use_case,
        event_bus=mock_event_bus,
    )

    violations_count = await uc.execute(target_date=target_date)

    # Phạt 3 học viên có mặt: 101, 102 và 888 (học viên đổi lớp)
    assert violations_count == 3
    mock_create_violation_use_case.execute.assert_called_once()
    penalized = mock_create_violation_use_case.execute.call_args.kwargs["user_ids"]
    assert set(penalized) == {101, 102, 888}
    assert 999 not in penalized  # Trainer không bị phạt
    assert 103 not in penalized  # Người vắng mặt không bị phạt
    assert 104 not in penalized  # Người nghỉ có phép không bị phạt


@pytest.mark.asyncio
async def test_check_overdue_duties_cancels_when_no_attendees_checked_in(
    mock_duty_repo,
    mock_meeting_repo,
    mock_team_repo,
    mock_create_violation_use_case,
    mock_event_bus,
):
    """Buổi học không có ai check-in (ví dụ cả lớp nghỉ / buổi học bị hủy) -> Ca chuyển CANCELLED, KHÔNG phạt ai."""
    target_date = date.today()
    duty = CleaningDuty(
        id=6,
        duty_date=target_date,
        team_id=12,
        meeting_id=101,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_pending_duties_for_date.return_value = [duty]

    # Meeting không có ai check-in
    meeting = Meeting(
        id=101,
        title="Buổi học AI",
        start_time=datetime(2026, 10, 19, 17, 30),
        end_time=datetime(2026, 10, 19, 19, 30),
        participants=[
            MeetingParticipant(user_id=101, check_in_at=None),
            MeetingParticipant(user_id=102, check_in_at=None),
            MeetingParticipant(
                user_id=888, check_in_at=None, status=ParticipantStatus.ABSENT_EXCUSED
            ),
        ],
    )
    mock_meeting_repo.get_by_id.return_value = meeting

    uc = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_use_case,
        event_bus=mock_event_bus,
    )

    violations_count = await uc.execute(target_date=target_date)

    assert violations_count == 0
    mock_create_violation_use_case.execute.assert_not_called()
    assert duty.status == DutyStatus.CANCELLED
    mock_duty_repo.save.assert_called_once_with(duty)


@pytest.mark.asyncio
async def test_check_overdue_duties_standalone_duty_penalizes_team_members(
    mock_duty_repo,
    mock_meeting_repo,
    mock_team_repo,
    mock_create_violation_use_case,
    mock_event_bus,
):
    """Ca trực tự do không có meeting: phạt tất cả thành viên trong nhóm trực."""
    target_date = date.today()
    duty = CleaningDuty(
        id=7,
        duty_date=target_date,
        team_id=12,
        meeting_id=None,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_pending_duties_for_date.return_value = [duty]

    uc = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_use_case,
        event_bus=mock_event_bus,
    )

    violations_count = await uc.execute(target_date=target_date)

    assert violations_count == 3
    called_users = mock_create_violation_use_case.execute.call_args.kwargs["user_ids"]
    assert set(called_users) == {101, 102, 103}
    assert duty.status == DutyStatus.VIOLATED


@pytest.mark.asyncio
async def test_check_overdue_duties_standalone_cancels_if_team_has_no_members(
    mock_duty_repo,
    mock_meeting_repo,
    mock_team_repo,
    mock_create_violation_use_case,
    mock_event_bus,
):
    """Ca trực tự do nhưng nhóm không có thành viên nào -> Chuyển CANCELLED."""
    target_date = date.today()
    duty = CleaningDuty(
        id=8,
        duty_date=target_date,
        team_id=99,
        meeting_id=None,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_pending_duties_for_date.return_value = [duty]

    mock_empty_team = MagicMock()
    mock_empty_team.member_ids = []
    mock_empty_team.members = []
    mock_team_repo.get_by_id.return_value = mock_empty_team

    uc = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_use_case,
        event_bus=mock_event_bus,
    )

    violations_count = await uc.execute(target_date=target_date)

    assert violations_count == 0
    mock_create_violation_use_case.execute.assert_not_called()
    assert duty.status == DutyStatus.CANCELLED


@pytest.mark.asyncio
async def test_check_overdue_duties_penalizes_rejected_duty_not_resubmitted(
    mock_duty_repo,
    mock_meeting_repo,
    mock_team_repo,
    mock_create_violation_use_case,
    mock_event_bus,
):
    """Ca trực bị REJECTED mà đến 23:59 không nộp lại -> bị phạt."""
    target_date = date.today()
    duty = CleaningDuty(
        id=9,
        duty_date=target_date,
        team_id=12,
        meeting_id=None,
        status=DutyStatus.REJECTED,
    )
    mock_duty_repo.get_pending_duties_for_date.return_value = [duty]

    uc = CheckOverdueDutiesUseCase(
        duty_repo=mock_duty_repo,
        meeting_repo=mock_meeting_repo,
        team_repo=mock_team_repo,
        create_violation_use_case=mock_create_violation_use_case,
        event_bus=mock_event_bus,
    )

    violations_count = await uc.execute(target_date=target_date)

    assert violations_count == 3
    assert duty.status == DutyStatus.VIOLATED


@pytest.mark.asyncio
async def test_submit_duty_evidence_validation_no_images(
    mock_duty_repo, mock_team_repo, mock_minio_service, mock_event_bus
):
    """Nộp minh chứng mà không gửi ảnh nào -> ném HTTPException 400."""
    duty = CleaningDuty(
        id=1,
        duty_date=date.today(),
        team_id=12,
        status=DutyStatus.PENDING,
        evidence_image_urls=[],
    )
    mock_duty_repo.get_by_id.return_value = duty

    uc = SubmitDutyEvidenceUseCase(
        duty_repo=mock_duty_repo,
        team_repo=mock_team_repo,
        minio_service=mock_minio_service,
        event_bus=mock_event_bus,
    )

    with pytest.raises(HTTPException) as exc_info:
        await uc.execute(
            duty_id=1,
            user_id=101,
            files=[],
            checklist=[{"id": "floor", "title": "Lau sàn", "checked": True}],
            is_admin=True,
        )

    assert exc_info.value.status_code == 400
    assert "tải lên ít nhất 1 ảnh" in exc_info.value.detail


@pytest.mark.asyncio
async def test_submit_duty_evidence_validation_no_checklist(
    mock_duty_repo, mock_team_repo, mock_minio_service, mock_event_bus
):
    """Nộp minh chứng mà không tích chọn bất kỳ hạng mục nào -> ném HTTPException 400."""
    duty = CleaningDuty(
        id=1,
        duty_date=date.today(),
        team_id=12,
        status=DutyStatus.PENDING,
        evidence_image_urls=[],
        checklist=[{"id": "floor", "title": "Lau sàn", "checked": False}],
    )
    mock_duty_repo.get_by_id.return_value = duty

    mock_file = MagicMock()
    mock_file.filename = "clean.jpg"

    uc = SubmitDutyEvidenceUseCase(
        duty_repo=mock_duty_repo,
        team_repo=mock_team_repo,
        minio_service=mock_minio_service,
        event_bus=mock_event_bus,
    )

    with pytest.raises(HTTPException) as exc_info:
        await uc.execute(
            duty_id=1,
            user_id=101,
            files=[mock_file],
            checklist=[{"id": "floor", "title": "Lau sàn", "checked": False}],
            is_admin=True,
        )

    assert exc_info.value.status_code == 400
    assert "tích chọn ít nhất 1 đầu việc" in exc_info.value.detail


@pytest.mark.asyncio
async def test_submit_duty_evidence_not_found(
    mock_duty_repo, mock_team_repo, mock_minio_service, mock_event_bus
):
    """Nộp minh chứng cho ca trực không tồn tại -> ném HTTPException 404."""
    mock_duty_repo.get_by_id.return_value = None
    mock_file = MagicMock()
    mock_file.filename = "clean.jpg"

    uc = SubmitDutyEvidenceUseCase(
        duty_repo=mock_duty_repo,
        team_repo=mock_team_repo,
        minio_service=mock_minio_service,
        event_bus=mock_event_bus,
    )

    with pytest.raises(HTTPException) as exc_info:
        await uc.execute(
            duty_id=9999,
            user_id=101,
            files=[mock_file],
            checklist=[{"id": "floor", "title": "Lau sàn", "checked": True}],
            is_admin=True,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_duty_success(mock_duty_repo, mock_team_repo):
    """Cập nhật ca trực nhật: checklist, note, team."""
    duty = CleaningDuty(
        id=1,
        duty_date=date(2026, 10, 20),
        team_id=12,
        status=DutyStatus.PENDING,
        note="Ghi chú cũ",
    )
    mock_duty_repo.get_by_id.return_value = duty
    mock_duty_repo.save.side_effect = lambda d: d

    uc = UpdateDutyUseCase(duty_repo=mock_duty_repo, team_repo=mock_team_repo)
    req = UpdateDutyRequest(
        checklist=[{"id": "fans", "title": "Lau quạt", "checked": True}],
        note="Phân công mới",
    )
    result = await uc.execute(duty_id=1, req=req)

    assert any(
        item["title"] == "Lau quạt" and item["checked"] for item in result.checklist
    )
    assert result.note == "Phân công mới"


@pytest.mark.asyncio
async def test_duty_notification_handler_submitted_event(
    mock_notification_service,
    mock_user_repo,
    mock_team_repo,
    mock_meeting_repo,
    mock_duty_repo,
    monkeypatch,
):
    """Test DutyNotificationHandler khi nhận event DutySubmitted."""
    monkeypatch.setattr(
        "app.duty.notification_handler.settings.DISCORD_PERMISSION_ROOM_ID", "123456789"
    )
    handler = DutyNotificationHandler(
        dispatcher=mock_notification_service,
        user_repo=mock_user_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
        duty_repo=mock_duty_repo,
    )

    event = DutySubmitted(
        duty_id=1,
        team_id=12,
        duty_date="20/10/2026",
        submitted_by=101,
        image_count=2,
        submitted_at="20/10/2026 21:00",
    )

    # Chạy trực tiếp worker task để test sync
    await handler._send_submitted_notification_task(event)

    mock_notification_service.dispatch_room.assert_called_once()
    payload = mock_notification_service.dispatch_room.call_args.kwargs["payload"]
    assert "Trần Thị Tuyết Trinh" in payload.content
    assert "20/10/2026" in payload.content


@pytest.mark.asyncio
async def test_duty_notification_handler_handles_exceptions_gracefully(
    mock_notification_service,
    mock_user_repo,
    mock_team_repo,
    mock_meeting_repo,
    mock_duty_repo,
):
    """Test DutyNotificationHandler không ném lỗi unhandled khi service fail."""
    mock_notification_service.dispatch_room.side_effect = Exception(
        "Discord network error"
    )
    handler = DutyNotificationHandler(
        dispatcher=mock_notification_service,
        user_repo=mock_user_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
        duty_repo=mock_duty_repo,
    )

    event = DutySubmitted(
        duty_id=1,
        team_id=12,
        duty_date="20/10/2026",
        submitted_by=101,
        image_count=2,
        submitted_at="20/10/2026 21:00",
    )

    # Không được raise exception
    await handler._send_submitted_notification_task(event)


@pytest.mark.asyncio
async def test_violation_notification_handler_sends_user_notification(
    mock_notification_service,
):
    """Test ViolationNotificationHandler gửi thông báo cá nhân khi có ViolationCreated."""
    handler = ViolationNotificationHandler(dispatcher=mock_notification_service)

    event = ViolationCreated(
        violation_id=10,
        user_id=101,
        user_name="Trần Thị Tuyết Trinh",
        reason="Có mặt tại buổi học nhưng không hoàn thành trực nhật phòng Lab ngày 20/10/2026",
        date="2026-10-20T23:59:00",
        creator_name="Hệ thống",
    )

    await handler._send_notifications_task(event)

    mock_notification_service.dispatch.assert_called_once()
    payload = mock_notification_service.dispatch.call_args.args[0]
    assert payload.user_id == 101
    assert "THÔNG BÁO VI PHẠM KỶ LUẬT" in payload.title
    assert "không hoàn thành trực nhật" in payload.fields[0]["value"]


@pytest.mark.asyncio
async def test_batch_create_duty_use_case(mock_duty_repo, mock_team_repo):
    """Test tạo ca trực nhật tự do cho nhiều nhóm cùng lúc kèm giờ bắt đầu & kết thúc."""
    mock_duty_repo.save.side_effect = lambda duty: CleaningDuty(
        id=101,
        duty_date=duty.duty_date,
        start_time=duty.start_time,
        end_time=duty.end_time,
        team_id=duty.team_id,
        team_name=duty.team_name,
        status=duty.status,
        checklist=duty.checklist,
        note=duty.note,
    )

    mock_event_bus = MagicMock()
    mock_event_bus.publish = AsyncMock()

    uc = BatchCreateDutyUseCase(
        duty_repo=mock_duty_repo,
        team_repo=mock_team_repo,
        event_bus=mock_event_bus,
    )

    results = await uc.execute(
        team_ids=[12, 13],
        duty_date=date(2026, 10, 20),
        start_time=time(17, 0),
        end_time=time(18, 30),
        checklist=[{"id": "1", "title": "Quét sàn", "checked": True}],
        note="Phân công nhiều nhóm cùng dọn",
    )

    assert len(results) == 1
    assert results[0].team_id == [12, 13]
    assert results[0].start_time == time(17, 0)
    assert results[0].end_time == time(18, 30)


@pytest.mark.asyncio
async def test_update_duty_use_case_with_time(mock_duty_repo, mock_team_repo):
    """Test cập nhật giờ bắt đầu và kết thúc của ca trực."""
    existing_duty = CleaningDuty(
        id=1,
        duty_date=date(2026, 10, 20),
        team_id=12,
        team_name="Team 12",
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_id.return_value = existing_duty
    mock_duty_repo.save.side_effect = lambda d: d

    uc = UpdateDutyUseCase(duty_repo=mock_duty_repo, team_repo=mock_team_repo)

    req = UpdateDutyRequest(
        start_time=time(18, 0),
        end_time=time(19, 0),
        note="Cập nhật giờ",
    )
    result = await uc.execute(duty_id=1, req=req)

    assert result.start_time == time(18, 0)
    assert result.end_time == time(19, 0)
    assert result.note == "Cập nhật giờ"


def test_get_weekly_schedule_detects_time_conflict(
    mock_duty_repo, mock_team_repo, mock_meeting_repo
):
    """Test hệ thống phát hiện và gắn cờ is_time_conflict khi 2 ca của cùng 1 nhóm bị trùng khung giờ."""
    # Giả sử trong tuần có 2 ca trực tự do của cùng nhóm 12 vào ngày Thứ 3 (2026-10-20):
    # Ca 1: 17:00 - 18:30
    # Ca 2: 18:00 - 19:30 (Trùng nhau khoảng 18:00 - 18:30)
    duty_1 = CleaningDuty(
        id=1,
        duty_date=date(2026, 10, 20),
        start_time=time(17, 0),
        end_time=time(18, 30),
        team_id=12,
        team_name="Gen 2 - Nhóm 1",
        status=DutyStatus.PENDING,
    )
    duty_2 = CleaningDuty(
        id=2,
        duty_date=date(2026, 10, 20),
        start_time=time(18, 0),
        end_time=time(19, 30),
        team_id=12,
        team_name="Gen 2 - Nhóm 1",
        status=DutyStatus.PENDING,
    )

    mock_meeting_repo.get_by_date_range.return_value = []
    mock_duty_repo.get_by_date_range.return_value = [duty_1, duty_2]
    mock_team = MagicMock()
    mock_team.id = 12
    mock_team.team_name = "Gen 2 - Nhóm 1"
    mock_team.members = []
    mock_team_repo.get_all_with_members.return_value = [mock_team]

    uc = GetDutiesUseCase(
        repo=mock_duty_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
    )

    weekly = uc.get_weekly_schedule(target_date=date(2026, 10, 20))

    assert len(weekly) == 2
    assert weekly[0].is_time_conflict is True
    assert weekly[1].is_time_conflict is True
    assert "Trùng khung giờ" in (weekly[0].conflict_message or "")
    assert "Trùng khung giờ" in (weekly[1].conflict_message or "")


@pytest.mark.asyncio
async def test_duty_notification_handler_scheduled_event_with_meeting_includes_transferred_students(
    mock_notification_service,
    mock_user_repo,
    mock_team_repo,
    mock_meeting_repo,
    mock_duty_repo,
    monkeypatch,
):
    """
    Test gửi thông báo khi tạo lịch trực nhật có gắn Meeting:
    - Phải gửi cho học viên chính thức trong meeting (id=101).
    - Phải gửi cho học viên từ lớp khác đổi ca sang (id=102).
    - Bỏ qua học viên đã xin nghỉ phép (id=103).
    - Bỏ qua Trainer/Người tạo meeting (id=999).
    """
    monkeypatch.setattr(
        "app.duty.notification_handler.settings.DISCORD_PERMISSION_ROOM_ID",
        "room_discord_123",
    )

    mock_meeting = MagicMock()
    mock_meeting.id = 500
    mock_meeting.created_by = 999
    mock_meeting.start_time = datetime(2026, 10, 22, 17, 30)
    mock_meeting.end_time = datetime(2026, 10, 22, 19, 30)

    # Danh sách participant gồm:
    # 1. Học viên chính thức (101)
    # 2. Học viên đổi ca sang (102)
    # 3. Học viên xin nghỉ phép hợp lệ (103)
    # 4. Trainer tạo meeting (999)
    p1 = MeetingParticipant(user_id=101, status=ParticipantStatus.NOT_JOINED)
    p2 = MeetingParticipant(user_id=102, status=ParticipantStatus.NOT_JOINED)
    p3 = MeetingParticipant(user_id=103, status=ParticipantStatus.ABSENT_EXCUSED)
    p4 = MeetingParticipant(user_id=999, status=ParticipantStatus.NOT_JOINED)
    mock_meeting.participants = [p1, p2, p3, p4]

    mock_meeting_repo.get_by_id.return_value = mock_meeting

    duty = CleaningDuty(
        id=77,
        duty_date=date(2026, 10, 22),
        start_time=time(17, 30),
        end_time=time(19, 30),
        team_id=[12],
        team_name="Gen 2 - thứ 5",
        meeting_id=500,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_id.return_value = duty

    handler = DutyNotificationHandler(
        dispatcher=mock_notification_service,
        user_repo=mock_user_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
        duty_repo=mock_duty_repo,
    )

    event = DutyScheduled(
        duty_id=77,
        team_id=[12],
        team_name="Gen 2 - thứ 5",
        duty_date="2026-10-22",
        meeting_id=500,
    )

    await handler._send_scheduled_notification_task(event)

    # Kiểm tra gửi thông báo cá nhân (dispatch)
    assert mock_notification_service.dispatch.call_count == 2
    sent_user_ids = [
        call.args[0].user_id
        for call in mock_notification_service.dispatch.call_args_list
    ]
    assert 101 in sent_user_ids
    assert 102 in sent_user_ids  # Học viên đổi ca sang phải nhận được thông báo
    assert 103 not in sent_user_ids  # Nghỉ phép không nhận
    assert 999 not in sent_user_ids  # Trainer không nhận

    # Theo yêu cầu: không gửi thông báo tóm tắt lên room Discord quản lý khi lên lịch
    mock_notification_service.dispatch_room.assert_not_called()


@pytest.mark.asyncio
async def test_duty_notification_handler_scheduled_event_standalone_free_duty(
    mock_notification_service,
    mock_user_repo,
    mock_team_repo,
    mock_meeting_repo,
    mock_duty_repo,
):
    """Test gửi thông báo khi tạo ca trực tự do (lấy theo thành viên của nhóm)."""
    mock_team = MagicMock()
    mock_team.id = 14
    mock_team.team_name = "Gen 2 - thứ 3"
    mock_team.member_ids = [201, 202]
    mock_team_repo.get_by_id.return_value = mock_team

    duty = CleaningDuty(
        id=88,
        duty_date=date(2026, 10, 22),
        start_time=time(15, 0),
        end_time=time(23, 0),
        team_id=[14],
        team_name="Gen 2 - thứ 3",
        meeting_id=None,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_id.return_value = duty

    handler = DutyNotificationHandler(
        dispatcher=mock_notification_service,
        user_repo=mock_user_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
        duty_repo=mock_duty_repo,
    )

    event = DutyScheduled(
        duty_id=88,
        team_id=[14],
        team_name="Gen 2 - thứ 3",
        duty_date="2026-10-22",
        meeting_id=None,
    )

    await handler._send_scheduled_notification_task(event)

    assert mock_notification_service.dispatch.call_count == 2
    sent_user_ids = [
        call.args[0].user_id
        for call in mock_notification_service.dispatch.call_args_list
    ]
    assert 201 in sent_user_ids
    assert 202 in sent_user_ids


@pytest.mark.asyncio
async def test_update_duty_use_case_publishes_duty_updated(
    mock_duty_repo, mock_team_repo
):
    """Kiểm tra UpdateDutyUseCase publish event DutyUpdated khi Admin/HR cập nhật ca trực."""
    mock_event_bus = MagicMock()
    mock_event_bus.publish = AsyncMock()

    mock_team = MagicMock()
    mock_team.team_name = "Gen 2 - thứ 4"
    mock_team_repo.get_by_id.return_value = mock_team

    existing_duty = CleaningDuty(
        id=99,
        duty_date=date(2026, 10, 20),
        start_time=time(17, 30),
        end_time=time(19, 30),
        team_id=[14],
        team_name="Gen 2 - thứ 4",
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_id.return_value = existing_duty
    mock_duty_repo.save.return_value = existing_duty

    use_case = UpdateDutyUseCase(
        duty_repo=mock_duty_repo,
        team_repo=mock_team_repo,
        event_bus=mock_event_bus,
    )

    req = UpdateDutyRequest(
        duty_date=date(2026, 10, 22),
        start_time=time(18, 0),
        end_time=time(20, 0),
        note="Đổi sang tối thứ 5 nhé",
    )

    res = await use_case.execute(duty_id=99, req=req)

    assert res.id == 99
    assert mock_event_bus.publish.call_count == 1
    published_event = mock_event_bus.publish.call_args[0][0]
    assert isinstance(published_event, DutyUpdated)
    assert published_event.duty_id == 99
    assert published_event.duty_date == "2026-10-22"
    assert published_event.is_time_changed is True


@pytest.mark.asyncio
async def test_duty_notification_handler_meeting_updated_reschedules_duty_and_notifies(
    mock_notification_service,
    mock_user_repo,
    mock_team_repo,
    mock_meeting_repo,
    mock_duty_repo,
):
    """Kiểm tra khi lịch meeting thay đổi ngày/giờ -> tự động cập nhật ca trực liên kết và gửi thông báo mới cho học viên."""
    mock_team = MagicMock()
    mock_team.id = 12
    mock_team.team_name = "Gen 2 - thứ 3 - 17h30 - 19h30"
    mock_team.members = [MagicMock(user_id=101), MagicMock(user_id=102)]
    mock_team_repo.get_all_with_members.return_value = [mock_team]
    mock_team_repo.get_by_id.return_value = mock_team

    mock_meeting = MagicMock()
    mock_meeting.id = 500
    mock_meeting.title = "Sinh hoạt định kỳ Gen 2"
    mock_meeting.created_by = 999
    p1 = MeetingParticipant(user_id=101, status=ParticipantStatus.NOT_JOINED)
    p2 = MeetingParticipant(user_id=102, status=ParticipantStatus.NOT_JOINED)
    p3 = MeetingParticipant(user_id=999, status=ParticipantStatus.NOT_JOINED)  # trainer
    mock_meeting.participants = [p1, p2, p3]
    mock_meeting_repo.get_by_id.return_value = mock_meeting

    linked_duty = CleaningDuty(
        id=77,
        duty_date=date(2026, 10, 20),
        start_time=time(17, 30),
        end_time=time(19, 30),
        team_id=[12],
        team_name="Gen 2 - thứ 3 - 17h30 - 19h30",
        meeting_id=500,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_meeting_id.return_value = [linked_duty]
    mock_duty_repo.save.return_value = linked_duty

    handler = DutyNotificationHandler(
        dispatcher=mock_notification_service,
        user_repo=mock_user_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
        duty_repo=mock_duty_repo,
    )

    # Meeting được đổi sang ngày 2026-10-23 từ 18:00 đến 20:00
    event = MeetingUpdated(
        meeting_id=500,
        title="Sinh hoạt định kỳ Gen 2",
        user_ids=[101, 102],
        start_time="2026-10-23T18:00:00",
        end_time="2026-10-23T20:00:00",
    )

    await handler._send_meeting_rescheduled_notification_task(event)

    # 1. Ca trực linked_duty phải được tự động cập nhật ngày & giờ mới
    assert mock_duty_repo.save.call_count == 1
    assert linked_duty.duty_date == date(2026, 10, 23)
    assert linked_duty.start_time == time(18, 0)
    assert linked_duty.end_time == time(20, 0)

    # 2. Thông báo phải được gửi đến 2 học viên (101, 102), bỏ qua trainer (999)
    assert mock_notification_service.dispatch.call_count == 2
    sent_user_ids = [
        call.args[0].user_id
        for call in mock_notification_service.dispatch.call_args_list
    ]
    assert 101 in sent_user_ids
    assert 102 in sent_user_ids

    payload = mock_notification_service.dispatch.call_args_list[0].args[0]
    assert "ĐIỀU CHỈNH LỊCH TRỰC NHẬT" in payload.title
    assert "23/10/2026" in payload.content


@pytest.mark.asyncio
async def test_duty_notification_handler_duty_updated_free_schedule(
    mock_notification_service,
    mock_user_repo,
    mock_team_repo,
    mock_meeting_repo,
    mock_duty_repo,
):
    """Kiểm tra khi ca trực tự do được cập nhật -> gửi thông báo thời gian mới cho học viên trong nhóm."""
    mock_team = MagicMock()
    mock_team.id = 15
    mock_team.team_name = "Gen 2 - thứ 5"
    mock_team.member_ids = [301, 302]
    mock_team_repo.get_by_id.return_value = mock_team

    duty = CleaningDuty(
        id=123,
        duty_date=date(2026, 10, 24),
        start_time=time(19, 0),
        end_time=time(21, 0),
        team_id=[15],
        team_name="Gen 2 - thứ 5",
        meeting_id=None,
        status=DutyStatus.PENDING,
        note="Vui lòng lau kính và tưới cây",
    )
    mock_duty_repo.get_by_id.return_value = duty

    handler = DutyNotificationHandler(
        dispatcher=mock_notification_service,
        user_repo=mock_user_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
        duty_repo=mock_duty_repo,
    )

    event = DutyUpdated(
        duty_id=123,
        team_id=[15],
        team_name="Gen 2 - thứ 5",
        duty_date="2026-10-24",
        meeting_id=None,
        is_time_changed=True,
    )

    await handler._send_duty_updated_notification_task(event)

    assert mock_notification_service.dispatch.call_count == 2
    sent_user_ids = [
        call.args[0].user_id
        for call in mock_notification_service.dispatch.call_args_list
    ]
    assert 301 in sent_user_ids
    assert 302 in sent_user_ids

    payload = mock_notification_service.dispatch.call_args_list[0].args[0]
    assert "CẬP NHẬT LỊCH TRỰC NHẬT" in payload.title
    assert "24/10/2026" in payload.content


@pytest.mark.asyncio
async def test_meeting_rescheduled_excludes_absent_and_transferred_students(
    mock_notification_service,
    mock_user_repo,
    mock_team_repo,
    mock_meeting_repo,
    mock_duty_repo,
):
    """
    Kiểm tra logic nghiệp vụ:
    - Khi meeting bị dời lịch, hệ thống chỉ gửi thông báo ca trực nhật cho những học viên thực tế tham gia.
    - Học viên đã xin phép vắng (ABSENCE) hoặc đã đổi buổi chuyển đi (CHANGE_MEETING) KHÔNG được nhận thông báo.
    - Học viên đổi buổi chuyển ĐẾN meeting này ĐƯỢC nhận thông báo.
    """
    # Buổi meeting gồm user 101, 102, 103 (xin vắng), 104 (chuyển đi)
    mock_meeting = MagicMock()
    mock_meeting.id = 600
    mock_meeting.title = "Sinh hoạt Gen 2 thứ 3"
    mock_meeting.created_by = 999  # Trainer
    mock_p1 = MagicMock(user_id=101, is_deleted=False, status=ParticipantStatus.NOT_JOINED)
    mock_p2 = MagicMock(user_id=102, is_deleted=False, status=ParticipantStatus.NOT_JOINED)
    mock_p3 = MagicMock(user_id=103, is_deleted=False, status=ParticipantStatus.NOT_JOINED)
    mock_p4 = MagicMock(user_id=104, is_deleted=False, status=ParticipantStatus.NOT_JOINED)
    mock_meeting.participants = [mock_p1, mock_p2, mock_p3, mock_p4]
    mock_meeting_repo.get_by_id.return_value = mock_meeting

    linked_duty = CleaningDuty(
        id=77,
        duty_date=date(2026, 10, 20),
        start_time=time(17, 30),
        end_time=time(19, 30),
        team_id=[12],
        team_name="Gen 2 - thứ 3",
        meeting_id=600,
        status=DutyStatus.PENDING,
    )
    mock_duty_repo.get_by_meeting_id.return_value = [linked_duty]
    mock_duty_repo.save.return_value = linked_duty

    # Mock permission_repo: user 103 xin vắng, user 104 chuyển đi, user 105 chuyển đến
    mock_permission_repo = MagicMock()
    mock_permission_repo.get_all_excused_or_transferred_out_user_ids.return_value = {103, 104}
    mock_permission_repo.get_transferred_in_user_ids_by_meeting.return_value = {105}

    handler = DutyNotificationHandler(
        dispatcher=mock_notification_service,
        user_repo=mock_user_repo,
        team_repo=mock_team_repo,
        meeting_repo=mock_meeting_repo,
        duty_repo=mock_duty_repo,
        permission_repo=mock_permission_repo,
    )

    event = MeetingUpdated(
        meeting_id=600,
        title="Sinh hoạt Gen 2 thứ 3",
        user_ids=[101, 102, 103, 104],
        start_time="2026-10-23T18:00:00",
        end_time="2026-10-23T20:00:00",
    )

    await handler._send_meeting_rescheduled_notification_task(event)

    # Phải gửi cho 101, 102 và 105. Tuyệt đối KHÔNG gửi cho 103 (xin vắng) và 104 (chuyển đi)
    sent_user_ids = [
        call.args[0].user_id
        for call in mock_notification_service.dispatch.call_args_list
    ]
    assert 101 in sent_user_ids
    assert 102 in sent_user_ids
    assert 105 in sent_user_ids
    assert 103 not in sent_user_ids, "User xin vắng không được nhận thông báo ca trực nhật"
    assert 104 not in sent_user_ids, "User chuyển buổi không được nhận thông báo ca trực nhật"
    assert mock_notification_service.dispatch.call_count == 3


@pytest.mark.asyncio
async def test_submit_duty_evidence_allows_transferred_in_student(
    mock_duty_repo, mock_team_repo, mock_meeting_repo, monkeypatch
):
    """
    Kiểm tra: Bạn A thuộc Nhóm 2 nhưng chuyển ca sinh hoạt sang Nhóm 1.
    Khi nộp minh chứng ca trực nhật gắn với buổi họp của Nhóm 1:
    Bạn A ĐƯỢC PHÉP nộp minh chứng thành công vì có tên trong danh sách tham gia buổi họp đó.
    """
    monkeypatch.setattr(
        "app.duty.application.submit_duty_evidence_use_case.datetime",
        MagicMock(
            now=MagicMock(
                return_value=datetime(2026, 10, 24, 13, 0, 0, tzinfo=timezone.utc)
            ),
            combine=datetime.combine,
        ),
    )
    from app.duty.application.submit_duty_evidence_use_case import (
        SubmitDutyEvidenceUseCase,
    )

    # Nhóm 1 chỉ gồm các user [201, 202]
    mock_team = MagicMock()
    mock_team.id = 11
    mock_team.member_ids = [201, 202]
    mock_team_repo.get_by_id.return_value = mock_team

    # Buổi họp của Nhóm 1 gồm 201, 202 và Bạn A (user_id=105 chuyển từ Nhóm 2 sang)
    mock_meeting = MagicMock()
    mock_meeting.id = 700
    p1 = MagicMock(user_id=201, is_deleted=False, status=ParticipantStatus.NOT_JOINED)
    p2 = MagicMock(user_id=202, is_deleted=False, status=ParticipantStatus.NOT_JOINED)
    p_transferred = MagicMock(user_id=105, is_deleted=False, status=ParticipantStatus.NOT_JOINED)
    mock_meeting.participants = [p1, p2, p_transferred]
    mock_meeting_repo.get_by_id.return_value = mock_meeting

    duty = CleaningDuty(
        id=99,
        duty_date=date(2026, 10, 24),
        team_id=[11],
        meeting_id=700,
        status=DutyStatus.PENDING,
        checklist=[{"task": "Quét sàn", "checked": True}],
    )
    mock_duty_repo.get_by_id.return_value = duty
    mock_duty_repo.save.return_value = duty

    mock_minio = MagicMock()
    mock_minio.upload_file = AsyncMock(return_value="https://minio.dut.vn/evidence.jpg")

    mock_event_bus = MagicMock()
    mock_event_bus.publish = AsyncMock()

    use_case = SubmitDutyEvidenceUseCase(
        duty_repo=mock_duty_repo,
        team_repo=mock_team_repo,
        minio_service=mock_minio,
        meeting_repo=mock_meeting_repo,
        event_bus=mock_event_bus,
    )

    mock_file = MagicMock()
    mock_file.filename = "evidence.jpg"
    mock_file.read = AsyncMock(return_value=b"image_bytes")

    # Bạn A (105) nộp minh chứng
    result = await use_case.execute(
        duty_id=99,
        user_id=105,
        files=[mock_file],
        checklist=[{"task": "Quét sàn", "checked": True}],
        note="Bạn A nhóm 2 học bù nộp thay",
        is_admin=False,
    )

    assert result.status == DutyStatus.AWAITING_APPROVAL
    assert mock_duty_repo.save.call_count == 1
    assert mock_event_bus.publish.call_count == 1


