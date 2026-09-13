"""
Meeting CRUD Use Cases — application layer.

Handles querying, creation, updating, and deletion of Meeting entities.
"""

from datetime import date, datetime, timedelta
from typing import cast

from fastapi import status

from app.core.config import settings
from app.meeting.application.checkin_use_cases import CheckInUseCase
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import MeetingCreated, MeetingUpdated
from app.meeting.infrastructure.repository import MeetingRepository
from app.meeting.schemas import MeetingUpdate
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.team.infrastructure.repository import TeamRepository


class GetMeetingsUseCase:
    """Lấy danh sách các buổi họp với bộ lọc"""

    def __init__(self, repo: MeetingRepository):
        self.repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: date | None = None,
        end_date: date | None = None,
        deleted: bool = False,
    ) -> list[Meeting]:
        filters = []
        if start_date:
            filters.append(
                FilterCriterion(
                    field="start_time", operator=FilterOperator.GTE, value=start_date
                )
            )
        if end_date:
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
        content: str | None = None,
        require_check_in: bool = True,
        user_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> Meeting:
        all_user_ids = set(user_ids or [])
        if team_ids:
            team_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)
            all_user_ids.update(team_user_ids)

        user_ids_list = list(all_user_ids)

        concurrent_participants = self.repo.get_concurrent_participants_count(
            start_time, end_time
        )

        needed_seats = len(user_ids_list)
        if concurrent_participants + needed_seats > settings.MAX_SEATS:
            remaining = max(0, settings.MAX_SEATS - concurrent_participants)
            raise BadRequestException(
                f"Chỗ ngồi không đủ, chỉ còn {remaining} chỗ ngồi"
            )

        participants = [MeetingParticipant(user_id=uid) for uid in user_ids_list]

        meeting = Meeting(
            title=title,
            start_time=start_time,
            end_time=end_time,
            content=content,
            require_check_in=require_check_in,
            participants=participants,
        )

        saved_meeting = self.repo.save(meeting)

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
    """Wrapper cho tất cả các use cases của Meeting module (giúp DI/Providers inject dễ dàng)."""

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

    def get_by_date(self, target_date: date) -> list[Meeting]:
        return self.repo.get_by_date(target_date)

    def get_all(self, **kwargs) -> list[Meeting]:
        return self.get_meetings.execute(**kwargs)

    def get_participating_meetings(
        self, user_id: int, month: int, year: int
    ) -> list[Meeting]:
        all_meetings = self.repo.get_all_with_participants(deleted=False)
        return [
            m for m in all_meetings if any(p.user_id == user_id for p in m.participants)
        ]

