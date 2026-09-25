from datetime import datetime
from typing import cast

from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import MeetingUpdated
from app.meeting.infrastructure.repository import MeetingRepository
from app.meeting.schemas import MeetingUpdate
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.team.infrastructure.repository import TeamRepository


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
