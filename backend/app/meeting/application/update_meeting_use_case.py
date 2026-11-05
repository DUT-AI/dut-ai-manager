from typing import cast

from app.meeting.domain.entity import Meeting
from app.meeting.domain.events import MeetingUpdated
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.meeting.schemas import MeetingUpdate
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus


class UpdateMeetingUseCase:
    """Cập nhật thông tin buổi họp và danh sách Trainer/Trainee"""

    def __init__(
        self,
        repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.participant_repo = participant_repo
        self.event_bus = event_bus

    async def execute(self, meeting_id: int, data: MeetingUpdate) -> Meeting:
        meeting = self.repo.get_with_participants(meeting_id)
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
        if data.enable_evaluation is not None:
            meeting.enable_evaluation = data.enable_evaluation

        if data.trainer_ids is not None or data.trainee_ids is not None:
            new_trainers_set = (
                set(data.trainer_ids)
                if data.trainer_ids is not None
                else {p.user_id for p in meeting.trainers}
            )
            new_trainees_set = (
                set(data.trainee_ids)
                if data.trainee_ids is not None
                else {p.user_id for p in meeting.trainees}
            )
            # Khử trùng lặp: Trainer ưu tiên hơn Trainee
            new_trainees_set = new_trainees_set - new_trainers_set

            self.participant_repo.sync_meeting_participants(
                meeting_id=meeting.id,
                new_trainers=new_trainers_set,
                new_trainees=new_trainees_set,
            )

        saved = self.repo.save(meeting)
        refreshed = self.repo.get_with_participants(meeting.id) or saved

        await self.event_bus.publish(
            cast(
                DomainEvent,
                MeetingUpdated(
                    meeting_id=cast(int, refreshed.id),
                    title=refreshed.title,
                    user_ids=[p.user_id for p in refreshed.participants],
                    start_time=refreshed.start_time.isoformat(),
                    end_time=refreshed.end_time.isoformat(),
                ),
            )
        )
        return refreshed
