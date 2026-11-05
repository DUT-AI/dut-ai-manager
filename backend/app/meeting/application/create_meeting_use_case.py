from datetime import datetime
from typing import cast

from app.core.config import settings
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import MeetingCreated
from app.meeting.domain.value_objects import ParticipantRole
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus


class CreateMeetingUseCase:
    """Tạo mới một buổi họp và phân loại Trainer, Trainee tham gia"""

    def __init__(
        self,
        repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.participant_repo = participant_repo
        self.event_bus = event_bus

    async def execute(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        creator_id: int,
        content: str | None = None,
        require_check_in: bool = True,
        enable_evaluation: bool = False,
        trainer_ids: list[int] | None = None,
        trainee_ids: list[int] | None = None,
    ) -> Meeting:
        trainers_set = set(trainer_ids or [])
        trainees_set = (
            set(trainee_ids or []) - trainers_set
        )  # Khử trùng lặp, ưu tiên TRAINER

        concurrent_participants = self.repo.get_concurrent_participants_count(
            start_time, end_time
        )

        needed_seats = len(trainers_set) + len(trainees_set)
        if concurrent_participants + needed_seats > settings.MAX_SEATS:
            remaining = max(0, settings.MAX_SEATS - concurrent_participants)
            raise BadRequestException(
                f"Chỗ ngồi không đủ, chỉ còn {remaining} chỗ ngồi"
            )

        participants = [
            MeetingParticipant(user_id=uid, role=ParticipantRole.TRAINER)
            for uid in trainers_set
        ] + [
            MeetingParticipant(user_id=uid, role=ParticipantRole.TRAINEE)
            for uid in trainees_set
        ]

        meeting = Meeting(
            title=title,
            start_time=start_time,
            end_time=end_time,
            content=content,
            require_check_in=require_check_in,
            enable_evaluation=enable_evaluation,
            participants=participants,
            created_by=creator_id,
        )

        saved_meeting = self.repo.save(meeting)
        if participants and saved_meeting.id:
            saved_participants = self.participant_repo.bulk_create(
                saved_meeting.id, participants
            )
            saved_meeting.participants = saved_participants

        all_user_ids = [p.user_id for p in participants]
        await self.event_bus.publish(
            cast(
                DomainEvent,
                MeetingCreated(
                    meeting_id=cast(int, saved_meeting.id),
                    title=saved_meeting.title,
                    user_ids=all_user_ids,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                ),
            )
        )

        return saved_meeting
