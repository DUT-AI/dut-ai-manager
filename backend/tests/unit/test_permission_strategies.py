from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.homework.domain.entity import Homework, HomeworkSubmission
from app.meeting.domain.entity import Meeting
from app.permission_request.application.strategies import (
    AbsenceStrategy,
    ChangeMeetingStrategy,
    LateStrategy,
    OtherStrategy,
    PermissionStrategyRegistry,
    PostponeStrategy,
)
from app.permission_request.application.update_permission_request_use_case import (
    UpdatePermissionRequestUseCase,
)
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import (
    AbsencePayload,
    ChangeMeetingPayload,
    LatePayload,
    OtherPayload,
    PostponePayload,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.model import (
    PermissionRequest as ORMPermissionRequest,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.permission_request.schemas import PermissionRequestUpdate


def test_strategy_registry_routing():
    """Kiểm tra Registry điều phối chính xác Strategy tương ứng với category."""
    repo = MagicMock()
    meeting_repo = MagicMock()
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()
    participant_repo = MagicMock()

    strategies = [
        AbsenceStrategy(repo, meeting_repo),
        LateStrategy(repo, meeting_repo),
        PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo),
        ChangeMeetingStrategy(repo, meeting_repo, participant_repo),
        OtherStrategy(),
    ]
    registry = PermissionStrategyRegistry(strategies)

    assert isinstance(registry.get(RequestCategory.ABSENCE), AbsenceStrategy)
    assert isinstance(registry.get(RequestCategory.LATE), LateStrategy)
    assert isinstance(registry.get(RequestCategory.POSTPONE), PostponeStrategy)
    assert isinstance(
        registry.get(RequestCategory.CHANGE_MEETING), ChangeMeetingStrategy
    )
    assert isinstance(registry.get(RequestCategory.OTHER), OtherStrategy)


def test_postpone_strategy_validation_happy_path():
    """Kiểm tra validation hợp lệ của PostponeStrategy cho lần hoãn đầu tiên."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    now = datetime.now(UTC)
    current_deadline = now + timedelta(days=2)
    hw = Homework(id=1, title="Bài tập Python")
    hw_repo.get_by_id.return_value = hw
    hw_assignee_repo.get_user_deadline.return_value = current_deadline
    hw_sub_repo.get_submissions_by_user.return_value = []
    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    # Gia hạn sau 2 ngày (hợp lệ <= 4 ngày)
    req_valid = PermissionRequest(
        created_by=1,
        note="Xin hoãn",
        payload=PostponePayload(
            homework_id=1,
            start_time=current_deadline + timedelta(days=2),
        ),
    )
    strategy.validate(req_valid)


def test_postpone_strategy_rejects_past_extended_deadline():
    """Kiểm tra từ chối khi thời gian gia hạn mới ở quá khứ."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    now = datetime.now(UTC)
    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    req = PermissionRequest(
        created_by=1,
        note="Xin hoãn",
        payload=PostponePayload(
            homework_id=1,
            start_time=now - timedelta(hours=1),
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req)
    assert exc_info.value.status_code == 400
    assert "Thời gian gia hạn mới phải ở tương lai" in exc_info.value.detail


def test_postpone_strategy_rejects_past_current_deadline():
    """Kiểm tra từ chối khi deadline hiện tại của học sinh đã quá hạn."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    now = datetime.now(UTC)
    past_deadline = now - timedelta(hours=2)
    hw = Homework(id=1, title="Bài tập Python")
    hw_repo.get_by_id.return_value = hw
    hw_assignee_repo.get_user_deadline.return_value = past_deadline
    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    req = PermissionRequest(
        created_by=1,
        note="Xin hoãn sau khi quá hạn",
        payload=PostponePayload(
            homework_id=1,
            start_time=now + timedelta(days=1),
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req)
    assert exc_info.value.status_code == 400
    assert "Bài tập đã quá hạn, không thể tạo đơn xin hoãn" in exc_info.value.detail


def test_postpone_strategy_rejects_already_completed_homework():
    """Kiểm tra từ chối khi học sinh đã hoàn thành đủ các bài tập yêu cầu."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    now = datetime.now(UTC)
    current_deadline = now + timedelta(days=2)
    hw = Homework(id=1, title="Bài tập Python")
    hw_repo.get_by_id.return_value = hw
    hw_assignee_repo.get_user_deadline.return_value = current_deadline
    hw_sub_repo.get_submissions_by_user.return_value = [
        HomeworkSubmission(
            homework_id=1,
            user_id=1,
            submission_type="CODING",
            is_passed=True,
            submitted_at=now,
        ),
        HomeworkSubmission(
            homework_id=1,
            user_id=1,
            submission_type="GAME",
            is_passed=True,
            submitted_at=now,
        ),
    ]
    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    req = PermissionRequest(
        created_by=1,
        note="Đã làm xong vẫn xin hoãn",
        payload=PostponePayload(
            homework_id=1,
            start_time=current_deadline + timedelta(days=2),
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req)
    assert exc_info.value.status_code == 400
    assert "Bạn đã hoàn thành bài tập này, không thể xin hoãn" in exc_info.value.detail


def test_postpone_strategy_cumulative_postpone_success():
    """Kiểm tra chấp thuận hoãn tích luỹ lần 2 nối tiếp khi chưa nộp bài và thời gian hợp lệ."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    now = datetime.now(UTC)
    # Giả sử sau lần 1 hoãn, deadline hiện tại đã dời tới now + 3 ngày
    postponed_deadline = now + timedelta(days=3)
    hw = Homework(id=1, title="Bài tập Python")
    hw_repo.get_by_id.return_value = hw
    hw_assignee_repo.get_user_deadline.return_value = postponed_deadline
    hw_sub_repo.get_submissions_by_user.return_value = []
    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    # Hoãn tích luỹ lần 2: xin dời thêm 3 ngày nữa (tổng cộng cách postponed_deadline là 3 ngày <= 4 ngày)
    req_cumulative = PermissionRequest(
        created_by=1,
        note="Xin hoãn lần 2",
        payload=PostponePayload(
            homework_id=1,
            start_time=postponed_deadline + timedelta(days=3),
        ),
    )
    strategy.validate(req_cumulative)


def test_postpone_strategy_rejects_exceeding_four_days():
    """Kiểm tra từ chối khi thời gian hoãn vượt quá 4 ngày so với deadline hiện tại."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    now = datetime.now(UTC)
    current_deadline = now + timedelta(days=2)
    hw = Homework(id=1, title="Bài tập Python")
    hw_repo.get_by_id.return_value = hw
    hw_assignee_repo.get_user_deadline.return_value = current_deadline
    hw_sub_repo.get_submissions_by_user.return_value = []
    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    req_invalid_exceed = PermissionRequest(
        created_by=1,
        note="Xin hoãn quá hạn",
        payload=PostponePayload(
            homework_id=1,
            start_time=current_deadline + timedelta(days=5),
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req_invalid_exceed)
    assert exc_info.value.status_code == 400
    assert "không được vượt quá 4 ngày" in exc_info.value.detail


def test_postpone_strategy_rejects_before_or_equal_current_deadline():
    """Kiểm tra từ chối khi thời gian gia hạn trước hoặc bằng deadline hiện tại."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    now = datetime.now(UTC)
    current_deadline = now + timedelta(days=2)
    hw = Homework(id=1, title="Bài tập Python")
    hw_repo.get_by_id.return_value = hw
    hw_assignee_repo.get_user_deadline.return_value = current_deadline
    hw_sub_repo.get_submissions_by_user.return_value = []
    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    req_invalid_equal = PermissionRequest(
        created_by=1,
        note="Xin hoãn bằng deadline hiện tại",
        payload=PostponePayload(
            homework_id=1,
            start_time=current_deadline,
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req_invalid_equal)
    assert exc_info.value.status_code == 400
    assert "Thời gian gia hạn mới phải sau deadline hiện tại" in exc_info.value.detail


@pytest.mark.asyncio
async def test_postpone_strategy_lifecycle():
    """Kiểm tra lifecycle của PostponeStrategy: on_created cập nhật deadline, on_deleted hoàn nguyên."""
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()
    initial_deadline = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
    hw_assignee_repo.get_user_deadline.return_value = initial_deadline

    strategy = PostponeStrategy(hw_repo, hw_assignee_repo, hw_sub_repo)

    new_deadline = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
    req = PermissionRequest(
        created_by=10,
        note="Xin hoãn bài tập 2 ngày",
        payload=PostponePayload(
            homework_id=5,
            start_time=new_deadline,
        ),
    )

    # 1. on_created: Cập nhật assignee deadline và lưu old_deadline
    await strategy.on_created(req, user_id=10)
    assert req.payload.old_deadline == initial_deadline
    hw_assignee_repo.update_deadline.assert_called_once_with(5, 10, new_deadline)

    # 2. on_deleted: Hoàn nguyên assignee deadline về old_deadline
    hw_assignee_repo.update_deadline.reset_mock()
    strategy.on_deleted(req, user_id=10)
    hw_assignee_repo.update_deadline.assert_called_once_with(5, 10, initial_deadline)


@pytest.mark.asyncio
async def test_absence_strategy_lifecycle():
    """Kiểm tra side-effects của AbsenceStrategy khi tạo và khi xóa."""
    repo = MagicMock()
    meeting_repo = MagicMock()
    meeting = Meeting(
        id=5,
        title="Họp hàng tuần",
        start_time=datetime(2026, 11, 1, 8, 0, tzinfo=UTC),
        end_time=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
    )
    meeting_repo.get_by_id.return_value = meeting
    strategy = AbsenceStrategy(repo, meeting_repo)

    req = PermissionRequest(
        created_by=10,
        note="Bận việc nhà",
        payload=AbsencePayload(meeting_id=5),
    )

    strategy.validate(req)
    await strategy.on_created(req, user_id=10)
    repo.mark_participant_excused.assert_called_once_with(5, 10)

    strategy.on_deleted(req, user_id=10)
    repo.revert_participant_excused.assert_called_once_with(5, 10)


@pytest.mark.asyncio
async def test_change_meeting_strategy_lifecycle():
    """Kiểm tra side-effects của ChangeMeetingStrategy khi tạo."""
    repo = MagicMock()
    meeting_repo = MagicMock()
    participant_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    meeting_b = Meeting(
        id=20,
        title="Meeting B",
        start_time=datetime(2026, 11, 2, 8, 0, tzinfo=UTC),
        end_time=datetime(2026, 11, 2, 10, 0, tzinfo=UTC),
        participants=[],
    )
    meeting_repo.get_meeting_with_lock.return_value = meeting_b
    strategy = ChangeMeetingStrategy(repo, meeting_repo, participant_repo, event_bus)

    req = PermissionRequest(
        id=99,
        created_by=15,
        note="Đổi sang ca chiều",
        payload=ChangeMeetingPayload(meeting_id=20, old_meeting_id=10),
    )

    await strategy.on_created(req, user_id=15)

    participant_repo.add_participant.assert_called_once()
    event_bus.publish.assert_awaited_once()


def test_orm_mapping_two_way_with_json_payload():
    """Kiểm tra ORM Model PermissionRequest ánh xạ 2 chiều với JSON payload."""
    now = datetime(2026, 10, 31, 8, 30, tzinfo=UTC)
    entity = PermissionRequest(
        id=123,
        created_by=45,
        note="Xin đi trễ có việc",
        payload=LatePayload(
            meeting_id=7,
            start_time=now,
        ),
    )

    orm_model = ORMPermissionRequest.from_entity(entity)
    assert orm_model.id == 123
    assert orm_model.category == RequestCategory.LATE
    assert orm_model.payload.meeting_id == 7

    # Chuyển ngược lại domain entity
    restored_entity = orm_model.to_entity()
    assert restored_entity.id == 123
    assert restored_entity.category == RequestCategory.LATE
    assert restored_entity.meeting_id == 7
    assert isinstance(restored_entity.payload, LatePayload)
    assert restored_entity.payload.meeting_id == 7


def test_permission_request_properties_pattern_matching():
    """Kiểm tra các properties truy xuất type-safe qua pattern matching trên entity."""
    now = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)

    # 1. Postpone
    req_postpone = PermissionRequest(
        id=1,
        created_by=10,
        note="Xin hoãn bài tập",
        payload=PostponePayload(homework_id=99, start_time=now),
    )
    assert req_postpone.category == RequestCategory.POSTPONE
    assert req_postpone.homework_id == 99
    assert req_postpone.meeting_id is None
    assert req_postpone.old_meeting_id is None
    assert req_postpone.start_time == now

    # 2. Change meeting
    req_change = PermissionRequest(
        id=2,
        created_by=10,
        note="Xin đổi ca",
        payload=ChangeMeetingPayload(
            meeting_id=20,
            old_meeting_id=10,
        ),
    )
    assert req_change.category == RequestCategory.CHANGE_MEETING
    assert req_change.homework_id is None
    assert req_change.meeting_id == 20
    assert req_change.old_meeting_id == 10
    assert req_change.start_time is None

    # 3. Absence
    req_absence = PermissionRequest(
        id=3,
        created_by=10,
        note="Xin vắng",
        payload=AbsencePayload(meeting_id=30),
    )
    assert req_absence.category == RequestCategory.ABSENCE
    assert req_absence.meeting_id == 30
    assert req_absence.homework_id is None
    assert req_absence.start_time is None

    # 4. Other
    req_other = PermissionRequest(
        id=4,
        created_by=10,
        note="Xin phép việc riêng",
        payload=OtherPayload(),
    )
    assert req_other.category == RequestCategory.OTHER
    assert req_other.meeting_id is None
    assert req_other.homework_id is None
    assert req_other.start_time is None


@pytest.mark.asyncio
async def test_update_permission_request_use_case_success_and_guardrails():
    """Kiểm tra cập nhật đơn xin phép và chặn thay đổi category/meeting trái phép."""
    repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    existing_req = PermissionRequest(
        id=10,
        created_by=5,
        note="Lý do ban đầu",
        payload=AbsencePayload(meeting_id=1),
    )
    repo.get_by_id.return_value = existing_req
    repo.save.side_effect = lambda req: req

    uc = UpdatePermissionRequestUseCase(repo=repo, event_bus=event_bus)

    # 1. Cập nhật note thành công
    updated = await uc.execute(
        request_id=10,
        data=PermissionRequestUpdate(note="Lý do mới đã sửa"),
    )
    assert updated.note == "Lý do mới đã sửa"
    repo.save.assert_called_once()
    event_bus.publish.assert_awaited_once()

    # 2. Cố tình thay đổi category -> Ném lỗi HTTPException 400
    with pytest.raises(HTTPException) as exc_info:
        await uc.execute(
            request_id=10,
            data=PermissionRequestUpdate(category=RequestCategory.LATE),
        )
    assert exc_info.value.status_code == 400
    assert "Không thể thay đổi loại đơn" in exc_info.value.detail

    # 3. Cố tình thay đổi meeting_id -> Ném lỗi HTTPException 400
    with pytest.raises(HTTPException) as exc_info:
        await uc.execute(
            request_id=10,
            data=PermissionRequestUpdate(meeting_id=999),
        )
    assert exc_info.value.status_code == 400
    assert "Không thể thay đổi buổi sinh hoạt" in exc_info.value.detail


def test_orm_model_typed_payload_parsing_and_casting():
    """Kiểm tra ORM model ép kiểu an toàn từ raw JSON payload (ISO str -> datetime, str -> int)."""
    now_dt = datetime.now(UTC)

    # 1. Late request với ISO string datetime
    orm_late = ORMPermissionRequest(
        id=1,
        category=RequestCategory.LATE,
        note="Đi trễ",
        payload={
            "meeting_id": 5,
            "start_time": "2026-11-01T08:30:00+00:00",
        },
        created_by=10,
        created_at=now_dt,
        updated_at=now_dt,
    )
    entity_late = orm_late.to_entity()
    assert isinstance(entity_late.payload, LatePayload)
    assert entity_late.payload.meeting_id == 5
    assert isinstance(entity_late.payload.start_time, datetime)
    assert entity_late.payload.start_time.year == 2026
    assert entity_late.payload.start_time.minute == 30

    # 2. Change meeting request với string numbers và ISO string datetime
    orm_change = ORMPermissionRequest(
        id=2,
        category=RequestCategory.CHANGE_MEETING,
        note="Đổi ca",
        payload={
            "meeting_id": "12",
            "old_meeting_id": "8",
            "start_time": "2026-11-02T14:00:00+00:00",
        },
        created_by=10,
        created_at=now_dt,
        updated_at=now_dt,
    )
    entity_change = orm_change.to_entity()
    assert isinstance(entity_change.payload, ChangeMeetingPayload)
    assert entity_change.payload.meeting_id == 12
    assert entity_change.payload.old_meeting_id == 8

    # 3. Postpone request với datetime object sẵn (in-memory)
    orm_postpone = ORMPermissionRequest(
        id=3,
        category=RequestCategory.POSTPONE,
        note="Hoãn bài",
        payload={
            "homework_id": 99,
            "start_time": now_dt,
        },
        created_by=10,
        created_at=now_dt,
        updated_at=now_dt,
    )
    entity_postpone = orm_postpone.to_entity()
    assert isinstance(entity_postpone.payload, PostponePayload)
    assert entity_postpone.payload.homework_id == 99
    assert entity_postpone.payload.start_time == now_dt


def test_count_by_user_category_month():
    """Kiểm tra đếm số đơn xin phép theo user, category và tháng/năm."""
    mock_session = MagicMock()
    mock_session.scalar.return_value = 2
    repo = PermissionRequestRepository(mock_session)

    count = repo.count_by_user_category_month(
        user_id=10,
        category=RequestCategory.ABSENCE,
        month=11,
        year=2026,
    )
    assert count == 2
    mock_session.scalar.assert_called_once()
    # Check that stmt was constructed
    call_arg = mock_session.scalar.call_args[0][0]
    compiled_str = str(call_arg)
    assert "permission_requests.created_by" in compiled_str
    assert "permission_requests.category" in compiled_str
    assert "permission_requests.is_deleted" in compiled_str


def test_payload_strict_validation_no_none():
    """Kiểm tra Pydantic Value Objects không chấp nhận None cho các trường bắt buộc."""
    from pydantic import ValidationError

    # 1. AbsencePayload yêu cầu meeting_id
    with pytest.raises(ValidationError):
        AbsencePayload()  # type: ignore[call-arg]

    # 2. LatePayload yêu cầu meeting_id và start_time
    with pytest.raises(ValidationError):
        LatePayload(meeting_id=1)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        LatePayload(start_time=datetime.now(UTC))  # type: ignore[call-arg]

    # 3. PostponePayload yêu cầu homework_id và start_time
    with pytest.raises(ValidationError):
        PostponePayload(homework_id=1)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        PostponePayload(start_time=datetime.now(UTC))  # type: ignore[call-arg]

    # 4. ChangeMeetingPayload yêu cầu meeting_id và old_meeting_id
    with pytest.raises(ValidationError):
        ChangeMeetingPayload(meeting_id=1)  # type: ignore[call-arg]


def test_orm_model_raises_on_invalid_raw_payload():
    """Kiểm tra ORMPermissionRequest chặn ngay khi raw payload thiếu dữ liệu bắt buộc."""
    from pydantic import ValidationError

    now_dt = datetime.now(UTC)

    # 1. ABSENCE thiếu meeting_id
    with pytest.raises((ValidationError, ValueError)):
        ORMPermissionRequest(
            id=1,
            category=RequestCategory.ABSENCE,
            note="Vắng",
            payload={"category": "ABSENCE"},
            created_by=10,
            created_at=now_dt,
            updated_at=now_dt,
        )

    # 2. LATE thiếu start_time
    with pytest.raises((ValidationError, ValueError)):
        ORMPermissionRequest(
            id=2,
            category=RequestCategory.LATE,
            note="Trễ",
            payload={"category": "LATE", "meeting_id": 10},
            created_by=10,
            created_at=now_dt,
            updated_at=now_dt,
        )

    # 3. POSTPONE thiếu homework_id
    with pytest.raises((ValidationError, ValueError)):
        ORMPermissionRequest(
            id=3,
            category=RequestCategory.POSTPONE,
            note="Hoãn",
            payload={"category": "POSTPONE", "start_time": "2026-11-20T10:00:00Z"},
            created_by=10,
            created_at=now_dt,
            updated_at=now_dt,
        )

    # 4. CHANGE_MEETING thiếu old_meeting_id
    with pytest.raises((ValidationError, ValueError)):
        ORMPermissionRequest(
            id=4,
            category=RequestCategory.CHANGE_MEETING,
            note="Đổi ca",
            payload={"category": "CHANGE_MEETING", "meeting_id": 10},
            created_by=10,
            created_at=now_dt,
            updated_at=now_dt,
        )

