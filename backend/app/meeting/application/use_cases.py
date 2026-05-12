from loguru import logger
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, cast

from app.core.config import settings
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import (
    MeetingAbsenceDetected,
    MeetingCreated,
    MeetingUpdated,
    ParticipantCheckedIn,
    ParticipantCheckedOut,
)
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.meeting.schemas import MeetingUpdate
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.shared.infrastructure.minio_service import MinioService
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time
from fastapi import UploadFile, status


class CheckMeetingAttendanceUseCase:
    """Kiểm tra điểm danh các buổi họp & tạo vi phạm tự động"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
    ):
        self.meeting_repo = meeting_repo
        self.permission_repo = permission_repo

    async def execute(self, target_date: Optional[date] = None):
        """
        Logic:
        1. Lấy tất cả các buổi họp diễn ra trong ngày hôm nay.
        2. Với mỗi buổi họp:
           - Duyệt qua danh sách người tham gia (participants).
           - Nếu người tham gia chưa điểm danh (status != ATTENDED):
             - Kiểm tra xem họ có đơn xin vắng (ABSENCE) cho ngày hôm đó không.
             - Nếu KHÔNG → tạo Vi phạm.
        """
        if target_date is None:
            now = get_current_utc7_time()
            target_date = now.date()

        meetings = self.meeting_repo.get_by_date(target_date)

        if not meetings:
            return 0

        # Tối ưu N+1: Thu thập toàn bộ user_id cần kiểm tra
        all_participant_user_ids = []
        for meeting in meetings:
            if not meeting.require_check_in:
                continue
            for participant in meeting.participants:
                if participant.status != ParticipantStatus.JOINED:
                    all_participant_user_ids.append(participant.user_id)

        # Lấy một lần duy nhất các user có đơn xin vắng
        absence_user_ids = self.permission_repo.get_user_ids_with_requests_for_date(
            user_ids=all_participant_user_ids,
            target_date=target_date,
            category=RequestCategory.ABSENCE,
        )

        created_count = 0
        for meeting in meetings:
            if not meeting.require_check_in:
                continue

            for participant in meeting.participants:
                # Nếu đã điểm danh xong (JOINED) thì bỏ qua
                if participant.status == ParticipantStatus.JOINED:
                    continue

                user_id = participant.user_id
                meeting_date = meeting.start_time.date()

                # Kiểm tra đơn xin vắng (Thao tác trong bộ nhớ trên tập hợp "set")
                if user_id in absence_user_ids:
                    continue

                # Phát sự kiện phát hiện vắng mặt không phép
                await EventBus.publish(
                    MeetingAbsenceDetected(
                        user_id=user_id,
                        meeting_id=meeting.id if meeting.id else 0,
                        meeting_title=meeting.title,
                        meeting_date=str(meeting_date),
                    )
                )
                created_count += 1

        return created_count


class GetMeetingsUseCase:
    """Lấy danh sách các buổi họp với bộ lọc"""

    def __init__(self, repo: MeetingRepository):
        self.repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        deleted: bool = False,
    ) -> List[Meeting]:
        filters = []
        if start_date:
            filters.append(
                FilterCriterion(
                    field="start_time", operator=FilterOperator.GTE, value=start_date
                )
            )
        if end_date:
            # Bao gồm cả ngày kết thúc bằng cách lấy mốc bắt đầu của ngày hôm sau và dùng toán tử LT (<)
            next_day = end_date + timedelta(days=1)
            filters.append(
                FilterCriterion(
                    field="start_time", operator=FilterOperator.LT, value=next_day
                )
            )

        qs = build_query_support(
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by="start_time",
            descending=True,
        )
        return self.repo.get_all_with_participants(query_support=qs, deleted=deleted)

    def get_by_id(self, meeting_id: int) -> Meeting:
        meeting = self.repo.get_with_participants(meeting_id)
        if not meeting:
            raise BadRequestException(
                "Không tìm thấy buổi họp", status_code=status.HTTP_404_NOT_FOUND
            )
        return meeting


class CreateMeetingUseCase:
    """Tạo mới một buổi họp và mời các thành viên tham gia"""

    def __init__(
        self,
        repo: MeetingRepository,
        team_repo: TeamRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.team_repo = team_repo
        self.event_bus = event_bus

    async def execute(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        content: Optional[str] = None,
        require_check_in: bool = True,
        user_ids: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None,
    ) -> Meeting:
        # Resolve team_ids to user_ids
        all_user_ids = set(user_ids or [])
        if team_ids:
            team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
            all_user_ids.update(team_user_ids)

        user_ids_list = list(all_user_ids)

        # Check overlapped meetings & seats (Business Rule)
        concurrent_participants = self.repo.get_concurrent_participants_count(
            start_time, end_time
        )

        needed_seats = len(user_ids_list)
        if concurrent_participants + needed_seats > settings.MAX_SEATS:
            remaining = max(0, settings.MAX_SEATS - concurrent_participants)
            raise BadRequestException(
                f"Chỗ ngồi không đủ, chỉ còn {remaining} chỗ ngồi"
            )

        # Create Domain Entity
        participants = [MeetingParticipant(user_id=uid) for uid in user_ids_list]

        meeting = Meeting(
            title=title,
            start_time=start_time,
            end_time=end_time,
            content=content,
            require_check_in=require_check_in,
            participants=participants,
        )

        # Persistence
        saved_meeting = self.repo.save(meeting)

        # Publish event for notifications
        await self.event_bus.publish(
            cast(
                DomainEvent,
                MeetingCreated(
                    meeting_id=cast(int, saved_meeting.id),
                    title=saved_meeting.title,
                    user_ids=user_ids_list,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                ),
            )
        )

        return saved_meeting


class CheckInUseCase:
    """Thực hiện điểm danh cho thành viên tham gia buổi họp"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        minio_service: MinioService,
        event_bus: type[EventBus] = EventBus,
    ):
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo
        self.minio_service = minio_service
        self.event_bus = event_bus

    async def execute(
        self, meeting_id: int, user_ids: List[int], image: UploadFile
    ) -> Tuple[List[MeetingParticipant], str]:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi họp")

        now = get_current_utc7_time()

        # 1. Upload image
        file_content = await image.read()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"meetings/{meeting_id}/checkin_{timestamp}_{image.filename}"

        image_url = self.minio_service.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=image.content_type or "image/jpeg",
        )

        # 2. Process check-in for each user
        updated_participants = []
        messages = []

        for user_id in user_ids:
            participant = self.participant_repo.get_by_meeting_and_user(
                meeting_id, user_id
            )
            if not participant:
                messages.append(f"Người dùng {user_id} không có trong danh sách")
                continue

            logger.debug(f"Participant: {participant}")

            if participant.status == ParticipantStatus.JOINED:
                logger.debug(
                    f"Người dùng {participant.user.name if participant.user else user_id} đã điểm danh"
                )
                messages.append(
                    f"Người dùng {participant.user.name if participant.user else user_id} đã điểm danh"
                )
                continue

            success, msg = participant.check_in(now, image_url)
            if not success:
                messages.append(msg)
                updated_participants.append(participant)
                continue

            # Logic: Lateness check & violation creation via events
            is_late = meeting.is_late(now)

            # Save participant state
            saved_p = self.participant_repo.save(participant)
            updated_participants.append(saved_p)
            messages.append(
                f"Đã ghi nhận {participant.user.name if participant.user else user_id}"
            )

            # Publish event (Violation Handler should handle lateness logic and permission requests)
            await self.event_bus.publish(
                cast(
                    DomainEvent,
                    ParticipantCheckedIn(
                        meeting_id=meeting_id,
                        user_id=user_id,
                        check_in_at=now,
                        is_late=is_late,
                        meeting_title=meeting.title,
                    ),
                )
            )

        return updated_participants, ". ".join(messages)


class CheckInWithCardUseCase:
    """Check-in bằng mã thẻ: tìm user → meeting trong cửa sổ ±30 phút quanh hiện tại."""

    def __init__(
        self,
        user_repo: UserRepository,
        participant_repo: ParticipantRepository,
        meeting_repo: MeetingRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.user_repo = user_repo
        self.participant_repo = participant_repo
        self.meeting_repo = meeting_repo
        self.event_bus = event_bus

    async def execute(self, card_code: str) -> str:
        code = (card_code or "").strip()
        if not code:
            raise BadRequestException("Ma the khong hop le")

        user = self.user_repo.get_by_check_in_card_code(code)
        if not user:
            raise BadRequestException(f"Dang ky {code} tren web")

        uid = user.id

        now = get_current_utc7_time()
        half_hour = timedelta(minutes=30)
        window_start = now - half_hour
        window_end = now + half_hour

        participant = self.participant_repo.find_participation_in_time_window(
            uid, window_start, window_end, now
        )
        if not participant or participant.meeting_id is None:
            raise BadRequestException("Khong ton tai meeting trong vong 30p")

        meeting = self.meeting_repo.get_domain_for_check_in(participant.meeting_id)
        if not meeting:
            raise BadRequestException("Khong ton tai meeting trong vong 30p")

        success, msg = participant.check_in(now, None)
        if not success:
            raise BadRequestException(msg)

        self.participant_repo.save(participant)
        is_late = meeting.is_late(now)
        await self.event_bus.publish(
            cast(
                DomainEvent,
                ParticipantCheckedIn(
                    meeting_id=participant.meeting_id,
                    user_id=uid,
                    check_in_at=now,
                    is_late=is_late,
                    meeting_title=meeting.title,
                ),
            )
        )
        return f"{user.name} checkin thành công"


class CheckOutUseCase:
    """Check-out khỏi buổi họp"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo
        self.event_bus = event_bus

    async def execute(self, meeting_id: int, user_id: int) -> MeetingParticipant:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi họp")

        participant = self.participant_repo.get_by_meeting_and_user(meeting_id, user_id)
        if not participant:
            raise BadRequestException("Bạn không có trong danh sách tham gia")

        if not participant.check_in_at:
            raise BadRequestException("Bạn chưa check-in")

        if participant.check_out_at:
            raise BadRequestException("Bạn đã check-out rồi")

        now = get_current_utc7_time()
        updated = self.participant_repo.check_out(participant.id, now)

        # Publish event
        await self.event_bus.publish(
            cast(
                DomainEvent,
                ParticipantCheckedOut(
                    meeting_id=meeting_id,
                    user_id=user_id,
                    check_out_at=now,
                    meeting_title=meeting.title,
                ),
            )
        )

        return updated


class UpdateMeetingUseCase:
    """Cập nhật thông tin buổi họp"""

    def __init__(
        self,
        repo: MeetingRepository,
        team_repo: TeamRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.team_repo = team_repo
        self.event_bus = event_bus

    async def execute(self, meeting_id: int, data: MeetingUpdate) -> Meeting:
        meeting = self.repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi họp")

        # Update fields if provided
        if data.title is not None:
            meeting.title = data.title
        if data.content is not None:
            meeting.content = data.content
        if data.start_time is not None:
            meeting.start_time = data.start_time
        if data.end_time is not None:
            meeting.end_time = data.end_time
        if data.require_check_in is not None:
            meeting.require_check_in = data.require_check_in

        # Handle participant updates if user_ids or team_ids provided
        if data.user_ids is not None or data.team_ids is not None:
            all_user_ids = set(data.user_ids or [])
            if data.team_ids:
                team_user_ids = self.team_repo.get_user_ids_by_teams(data.team_ids)
                all_user_ids.update(team_user_ids)

            user_ids_list = list(all_user_ids)

            existing_participants_map = {p.user_id: p for p in meeting.participants}
            new_participants = []

            for uid in user_ids_list:
                if uid in existing_participants_map:
                    new_participants.append(existing_participants_map[uid])
                else:
                    new_participants.append(MeetingParticipant(user_id=uid))

            meeting.participants = new_participants

        saved = self.repo.save(meeting)

        # Publish event
        await self.event_bus.publish(
            cast(
                DomainEvent,
                MeetingUpdated(
                    meeting_id=cast(int, saved.id),
                    title=saved.title,
                    user_ids=[p.user_id for p in saved.participants],
                    start_time=saved.start_time.isoformat(),
                    end_time=saved.end_time.isoformat(),
                ),
            )
        )
        return saved


class DeleteMeetingUseCase:
    """Xóa một buổi họp (Soft-delete)"""

    def __init__(self, repo: MeetingRepository):
        self.repo = repo

    def execute(self, meeting_id: int) -> bool:
        return self.repo.delete(meeting_id)


class MeetingUseCases:
    """Wrapper cho tất cả các use cases của Meeting module (giúp inject dễ dàng hơn vào các service khác)"""

    def __init__(
        self,
        get_meetings: GetMeetingsUseCase,
        create_meeting: CreateMeetingUseCase,
        update_meeting: UpdateMeetingUseCase,
        delete_meeting: DeleteMeetingUseCase,
        check_in: CheckInUseCase,
        repo: MeetingRepository,
    ):
        self.get_meetings = get_meetings
        self.create_meeting = create_meeting
        self.update_meeting = update_meeting
        self.delete_meeting = delete_meeting
        self.check_in = check_in
        self.repo = repo

    def get_by_id(self, meeting_id: int) -> Meeting:
        return self.get_meetings.get_by_id(meeting_id)

    def get_by_date(self, target_date: date) -> List[Meeting]:
        return self.repo.get_by_date(target_date)

    def get_all(self, **kwargs) -> List[Meeting]:
        return self.get_meetings.execute(**kwargs)

    def get_participating_meetings(
        self, user_id: int, month: int, year: int
    ) -> List[Meeting]:

        all_meetings = self.repo.get_all_with_participants(deleted=False)
        return [
            m for m in all_meetings if any(p.user_id == user_id for p in m.participants)
        ]
