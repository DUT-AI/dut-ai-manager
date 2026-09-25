from datetime import timedelta
from typing import cast

from app.meeting.application.checkin_use_case import parse_client_time_to_utc7_naive
from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.events import ParticipantCheckedOut
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.utils.datetime import get_current_utc7_time


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

    async def execute(
        self,
        user_id: int,
        client_time: str | None = None,
        client_event_id: str | None = None,
    ) -> list[MeetingParticipant]:
        now = get_current_utc7_time()

        check_out_dt = now
        if client_time:
            check_out_dt = parse_client_time_to_utc7_naive(client_time)

        half_hour = timedelta(minutes=30)
        window_start = now - half_hour
        window_end = now + half_hour

        participations = self.participant_repo.find_all_participations_in_time_window(
            user_id, window_start, window_end, now
        )

        updated_participants = []
        for participant in participations:
            if (
                participant.status == ParticipantStatus.COMPLETED
                and client_event_id
                and participant.client_event_id == client_event_id
            ):
                continue

            if not participant.check_in_at or participant.check_out_at:
                continue

            if (
                participant.check_in_at
                and check_out_dt.timestamp() < participant.check_in_at.timestamp()
            ):
                raise BadRequestException("check_out_at must be after check_in_at")

            meeting_id = participant.meeting_id
            if meeting_id is None:
                continue

            meeting = self.meeting_repo.get_domain_for_check_in(meeting_id)
            if not meeting:
                continue

            assert participant.id is not None
            pid = participant.id

            updated = self.participant_repo.check_out(pid, check_out_dt)
            if client_event_id:
                updated.client_event_id = client_event_id
                self.participant_repo.save(updated)

            updated_participants.append(updated)

            await self.event_bus.publish(
                cast(
                    DomainEvent,
                    ParticipantCheckedOut(
                        meeting_id=meeting_id,
                        user_id=user_id,
                        check_out_at=check_out_dt,
                        meeting_title=meeting.title,
                    ),
                )
            )

        if not updated_participants:
            raise BadRequestException(
                "Không tìm thấy buổi họp nào đang tham gia để check-out"
            )

        return updated_participants
