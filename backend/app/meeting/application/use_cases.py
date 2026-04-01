from datetime import date, datetime
from typing import List, Optional, Tuple

from app.core.config import settings
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import (MeetingCreated, MeetingUpdated,
                                       ParticipantCheckedIn)
from app.meeting.infrastructure.repository import (MeetingRepository,
                                                   ParticipantRepository)
from app.schemas.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.shared.infrastructure.minio_service import MinioService
from app.utils.datetime import get_current_utc7_time
from fastapi import UploadFile, status


class GetMeetingsUseCase:
    """Lấy danh sách các buổi họp với bộ lọc"""

    def __init__(self, repo: MeetingRepository):
        self.repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Meeting]:
        return self.repo.get_all_with_participants(
            skip, limit, month, year, start_date, end_date
        )

    def get_by_id(self, meeting_id: int) -> Meeting:
        meeting = self.repo.get_with_participants(meeting_id)
        if not meeting:
            raise BadRequestException(
                "Không tìm thấy buổi họp", status_code=status.HTTP_404_NOT_FOUND
            )
        return meeting


class CreateMeetingUseCase:
    """Tạo mới một buổi họp và mời các thành viên tham gia"""

    def __init__(self, repo: MeetingRepository, event_bus: type[EventBus] = EventBus):
        self.repo = repo
        self.event_bus = event_bus

    async def execute(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        content: Optional[str] = None,
        require_check_in: bool = True,
        user_ids: List[int] = None,
    ) -> Meeting:
        # Check overlapped meetings & seats (Business Rule)
        concurrent_participants = self.repo.get_concurrent_participants_count(
            start_time, end_time
        )

        needed_seats = len(user_ids) if user_ids else 0
        if concurrent_participants + needed_seats > settings.MAX_SEATS:
            remaining = max(0, settings.MAX_SEATS - concurrent_participants)
            raise BadRequestException(
                f"Chỗ ngồi không đủ, chỉ còn {remaining} chỗ ngồi"
            )

        # Create Domain Entity
        participants = [MeetingParticipant(user_id=uid) for uid in (user_ids or [])]

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
            MeetingCreated(
                meeting_id=saved_meeting.id,
                title=saved_meeting.title,
                user_ids=user_ids or [],
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
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
                ParticipantCheckedIn(
                    meeting_id=meeting_id,
                    user_id=user_id,
                    check_in_at=now,
                    is_late=is_late,
                    meeting_title=meeting.title,
                )
            )

        return updated_participants, ". ".join(messages)


class UpdateMeetingUseCase:
    """Cập nhật thông tin buổi họp"""

    def __init__(self, repo: MeetingRepository, event_bus: type[EventBus] = EventBus):
        self.repo = repo
        self.event_bus = event_bus

    async def execute(self, meeting_id: int, data: "MeetingUpdate") -> Meeting:
        from app.meeting.schemas import MeetingUpdate

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
        # (Logic này khá phức tạp, tạm thời giữ đơn giản bằng cách update entity)

        saved = self.repo.save(meeting)

        # Publish event
        await self.event_bus.publish(
            MeetingUpdated(
                meeting_id=saved.id,
                title=saved.title,
                user_ids=[p.user_id for p in saved.participants],
                start_time=saved.start_time.isoformat(),
                end_time=saved.end_time.isoformat(),
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
        """Tương đương với logic cũ trong MeetingService"""
        all_meetings = self.get_all(limit=1000, month=month, year=year)
        return [
            m for m in all_meetings if any(p.user_id == user_id for p in m.participants)
        ]
