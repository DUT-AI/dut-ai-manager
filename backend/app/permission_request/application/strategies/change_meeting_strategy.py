from datetime import UTC, datetime
from typing import cast
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.core.config import settings
from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.application.strategies.base import PermissionStrategy
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import MeetingParticipantTransferred
from app.permission_request.domain.payloads import ChangeMeetingPayload
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.domain.event_bus import DomainEvent, EventBus


class ChangeMeetingStrategy(PermissionStrategy[ChangeMeetingPayload]):
    """
    Chiến lược xử lý đơn đổi buổi sinh hoạt (CHANGE_MEETING).
    - Thẩm định điều kiện đổi ca (Meeting B chưa bắt đầu, còn ghế trống).
    - Tự động rút khỏi Meeting A (nếu có) và hủy các đơn vắng/trễ cũ tại Meeting A.
    - Tự động thêm vào Meeting B.
    - Phát sự kiện MeetingParticipantTransferred.
    """

    def __init__(
        self,
        permission_repo: PermissionRequestRepository,
        meeting_repo: MeetingRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.permission_repo = permission_repo
        self.meeting_repo = meeting_repo
        self.event_bus = event_bus

    @property
    def category(self) -> RequestCategory:
        return RequestCategory.CHANGE_MEETING

    def validate(self, request: PermissionRequest[ChangeMeetingPayload]) -> None:
        meeting_id = request.payload.meeting_id
        old_meeting_id = request.payload.old_meeting_id
        user_id = request.user_id

        if not meeting_id:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn buổi họp đích muốn chuyển đến",
            )

        if old_meeting_id is not None and old_meeting_id == meeting_id:
            raise HTTPException(
                status_code=400, detail="Không thể đổi sang cùng một buổi họp"
            )

        now = datetime.now(UTC)

        # 1. Khóa và lấy thông tin Meeting B (Meeting đích)
        meeting_b = self.meeting_repo.get_meeting_with_lock(meeting_id)
        if not meeting_b:
            raise HTTPException(status_code=404, detail="Không tìm thấy buổi họp đích")

        # 2. Kiểm tra thời hạn: Buổi B phải chưa bắt đầu
        target_start = (
            meeting_b.start_time
            if meeting_b.start_time.tzinfo is not None
            else meeting_b.start_time.replace(
                tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")
            ).astimezone(UTC)
        )
        if now >= target_start:
            raise HTTPException(
                status_code=400,
                detail="Không thể đổi sang buổi họp đã bắt đầu hoặc đã kết thúc",
            )

        # 3. Kiểm tra số ghế khả dụng của Meeting B
        absence_user_ids = self.permission_repo.get_absence_user_ids_by_meeting(
            meeting_id
        )
        available_seats = meeting_b.calculate_available_seats(
            max_seats=settings.MAX_SEATS,
            absence_user_ids=absence_user_ids,
        )

        is_already_in_b = any(
            p.user_id == user_id and not p.is_deleted for p in meeting_b.participants
        )
        if not is_already_in_b and available_seats <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Buổi họp đích đã hết chỗ ngồi (0/{settings.MAX_SEATS})",
            )

    async def on_created(
        self, request: PermissionRequest[ChangeMeetingPayload], user_id: int
    ) -> None:
        meeting_id = request.payload.meeting_id
        old_meeting_id = request.payload.old_meeting_id

        # 1. Xử lý rút khỏi Meeting A (nếu có old_meeting_id)
        if old_meeting_id:
            old_meeting = self.meeting_repo.get_with_participants(old_meeting_id)
            if old_meeting:
                old_meeting.participants = [
                    p for p in old_meeting.participants if p.user_id != user_id
                ]
                self.meeting_repo.save(old_meeting)

            # Tự động hủy đơn xin vắng / đi trễ cũ tại Meeting A
            self.permission_repo.cancel_active_requests_by_meeting(
                user_id=user_id, meeting_id=old_meeting_id
            )

        # 2. Thêm participant vào Meeting B
        meeting_b = self.meeting_repo.get_meeting_with_lock(meeting_id)
        if meeting_b:
            is_already_in_b = any(
                p.user_id == user_id and not p.is_deleted
                for p in meeting_b.participants
            )
            if not is_already_in_b:
                meeting_b.participants.append(
                    MeetingParticipant(
                        user_id=user_id,
                        meeting_id=meeting_id,
                        status=ParticipantStatus.NOT_JOINED,
                    )
                )
                self.meeting_repo.save(meeting_b)

        # 3. Phát sự kiện DomainEvent MeetingParticipantTransferred
        await self.event_bus.publish(
            cast(
                DomainEvent,
                MeetingParticipantTransferred(
                    request_id=cast(int, request.id),
                    user_id=user_id,
                    old_meeting_id=old_meeting_id,
                    new_meeting_id=meeting_id,
                    note=request.note,
                ),
            )
        )

    def on_deleted(
        self, request: PermissionRequest[ChangeMeetingPayload], user_id: int
    ) -> None:
        pass
