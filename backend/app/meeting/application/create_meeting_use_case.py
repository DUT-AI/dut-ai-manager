from datetime import datetime
from typing import cast

from app.core.config import settings
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import MeetingCreated
from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.team.infrastructure.repository import TeamRepository


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
