from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.homework.domain.entity import Homework
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
from app.permission_request.schemas import PermissionRequestUpdate


def test_strategy_registry_routing():
    """Kiểm tra Registry điều phối chính xác Strategy tương ứng với category."""
    repo = MagicMock()
    meeting_repo = MagicMock()
    hw_repo = MagicMock()

    strategies = [
        AbsenceStrategy(repo, meeting_repo),
        LateStrategy(repo, meeting_repo),
        PostponeStrategy(hw_repo),
        ChangeMeetingStrategy(repo, meeting_repo),
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


def test_postpone_strategy_validation():
    """Kiểm tra validation của PostponeStrategy."""
    hw_repo = MagicMock()
    deadline = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
    hw = Homework(
        id=1,
        title="Bài tập Python",
        deadline=deadline,
    )
    hw_repo.get_by_id.return_value = hw
    strategy = PostponeStrategy(hw_repo)

    # 1. Hợp lệ: gia hạn sau 2 ngày
    req_valid = PermissionRequest(
        user_id=1,
        note="Xin hoãn",
        payload=PostponePayload(
            homework_id=1,
            start_time=datetime(2026, 11, 3, 12, 0, tzinfo=UTC),
        ),
    )
    strategy.validate(req_valid)

    # 2. Quá 4 ngày -> lỗi
    req_invalid_exceed = PermissionRequest(
        user_id=1,
        note="Xin hoãn",
        payload=PostponePayload(
            homework_id=1,
            start_time=datetime(2026, 11, 6, 12, 0, tzinfo=UTC),
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        strategy.validate(req_invalid_exceed)
    assert exc_info.value.status_code == 400
    assert "không được vượt quá 4 ngày" in exc_info.value.detail


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
        user_id=10,
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
    strategy = ChangeMeetingStrategy(repo, meeting_repo, event_bus)

    req = PermissionRequest(
        id=99,
        user_id=15,
        note="Đổi sang ca chiều",
        payload=ChangeMeetingPayload(meeting_id=20, old_meeting_id=None),
    )

    await strategy.on_created(req, user_id=15)

    assert any(p.user_id == 15 for p in meeting_b.participants)
    meeting_repo.save.assert_called_once_with(meeting_b)
    event_bus.publish.assert_awaited_once()


def test_orm_mapping_two_way_with_json_payload():
    """Kiểm tra ORM Model PermissionRequest ánh xạ 2 chiều với JSON payload."""
    now = datetime(2026, 10, 31, 8, 30, tzinfo=UTC)
    entity = PermissionRequest(
        id=123,
        user_id=45,
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
    assert orm_model.payload["meeting_id"] == 7

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
        user_id=10,
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
        user_id=10,
        note="Xin đổi ca",
        payload=ChangeMeetingPayload(
            meeting_id=20,
            old_meeting_id=10,
            start_time=now,
        ),
    )
    assert req_change.category == RequestCategory.CHANGE_MEETING
    assert req_change.homework_id is None
    assert req_change.meeting_id == 20
    assert req_change.old_meeting_id == 10
    assert req_change.start_time == now

    # 3. Absence
    req_absence = PermissionRequest(
        id=3,
        user_id=10,
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
        user_id=10,
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
        user_id=5,
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
    assert isinstance(entity_change.payload.start_time, datetime)
    assert entity_change.payload.start_time.hour == 14

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

