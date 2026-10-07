from typing import cast

from fastapi import HTTPException

from app.core.config import settings
from app.core.context import get_current_user_id
from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import (
    MeetingParticipantTransferred,
    PermissionRequestCreated,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.utils.datetime import get_current_utc7_time


class CreateChangeMeetingRequestUseCase:
    """
    Use case xử lý đơn xin đổi buổi sinh hoạt (CHANGE_MEETING).
    - Kiểm tra thời gian buổi đích (Meeting B) trong tương lai.
    - Khóa giao dịch (Pessimistic Lock) và tính toán số ghế khả dụng.
    - Tự động duyệt ngay (Auto-Approve): rút khỏi Meeting A (nếu có), thêm vào Meeting B.
    - Tự động hủy đơn xin vắng/trễ cũ tại Meeting A.
    - Ghi nhận đơn PermissionRequest và phát sự kiện MeetingParticipantTransferred.
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

    async def execute(
        self,
        note: str,
        meeting_id: int,
        old_meeting_id: int | None = None,
        user_id: int | None = None,
    ) -> PermissionRequest:
        current_user_id = user_id or get_current_user_id()
        if not current_user_id:
            raise HTTPException(status_code=401, detail="Chưa xác thực danh tính người dùng")

        if old_meeting_id is not None and old_meeting_id == meeting_id:
            raise HTTPException(
                status_code=400, detail="Không thể đổi sang cùng một buổi họp"
            )

        now = get_current_utc7_time()

        # 1. Khóa và lấy thông tin Meeting B (Meeting đích)
        meeting_b = self.meeting_repo.get_meeting_with_lock(meeting_id)
        if not meeting_b:
            raise HTTPException(status_code=404, detail="Không tìm thấy buổi họp đích")

        # 2. Kiểm tra thời hạn: Buổi B phải chưa bắt đầu
        if now >= meeting_b.start_time:
            raise HTTPException(
                status_code=400,
                detail="Không thể đổi sang buổi họp đã bắt đầu hoặc đã kết thúc",
            )

        # 3. Kiểm tra số ghế khả dụng của Meeting B
        absence_user_ids = self.permission_repo.get_absence_user_ids_by_meeting(meeting_id)
        available_seats = meeting_b.calculate_available_seats(
            max_seats=settings.MAX_SEATS,
            absence_user_ids=absence_user_ids,
        )

        # Nếu user chưa có trong meeting_b và hết ghế -> Báo lỗi
        is_already_in_b = any(
            p.user_id == current_user_id and not p.is_deleted
            for p in meeting_b.participants
        )
        if not is_already_in_b and available_seats <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Buổi họp đích đã hết chỗ ngồi (0/{settings.MAX_SEATS})",
            )

        # 4. Xử lý rút khỏi Meeting A (nếu có old_meeting_id)
        if old_meeting_id:
            old_meeting = self.meeting_repo.get_with_participants(old_meeting_id)
            if old_meeting:
                # Lọc bỏ participant cũ
                old_meeting.participants = [
                    p for p in old_meeting.participants if p.user_id != current_user_id
                ]
                self.meeting_repo.save(old_meeting)

            # Tự động hủy đơn xin vắng / đi trễ cũ tại Meeting A
            self.permission_repo.cancel_active_requests_by_meeting(
                user_id=current_user_id, meeting_id=old_meeting_id
            )

        # 5. Thêm participant vào Meeting B
        if not is_already_in_b:
            meeting_b.participants.append(
                MeetingParticipant(
                    user_id=current_user_id,
                    meeting_id=meeting_id,
                    status=ParticipantStatus.NOT_JOINED,
                )
            )
            self.meeting_repo.save(meeting_b)

        # 6. Lưu bản ghi PermissionRequest loại CHANGE_MEETING
        request = PermissionRequest(
            user_id=current_user_id,
            created_by=current_user_id,
            category=RequestCategory.CHANGE_MEETING,
            note=note,
            meeting_id=meeting_id,
            old_meeting_id=old_meeting_id,
            start_time=now,
        )
        saved = self.permission_repo.save(request)

        # 7. Phát sự kiện DomainEvent
        await self.event_bus.publish(
            cast(
                DomainEvent,
                MeetingParticipantTransferred(
                    request_id=cast(int, saved.id),
                    user_id=current_user_id,
                    old_meeting_id=old_meeting_id,
                    new_meeting_id=meeting_id,
                    note=note,
                ),
            )
        )

        await self.event_bus.publish(
            cast(
                DomainEvent,
                PermissionRequestCreated(
                    request_id=cast(int, saved.id),
                    user_id=current_user_id,
                    category=saved.category,
                    note=saved.note,
                    start_time=saved.start_time,
                ),
            )
        )

        return saved
