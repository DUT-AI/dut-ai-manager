from typing import cast

from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import MeetingUpdated
from app.meeting.domain.value_objects import ParticipantRole
from app.meeting.infrastructure.repository import MeetingRepository
from app.meeting.schemas import MeetingUpdate
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus


class UpdateMeetingUseCase:
    """Cập nhật thông tin buổi họp và danh sách Trainer/Trainee"""

    def __init__(
        self,
        repo: MeetingRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
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
            existing_participants_map = {p.user_id: p for p in meeting.participants}

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

            new_participants: list[MeetingParticipant] = []

            for uid in new_trainers_set:
                if uid in existing_participants_map:
                    p = existing_participants_map[uid]
                    p.role = ParticipantRole.TRAINER
                    new_participants.append(p)
                else:
                    new_participants.append(
                        MeetingParticipant(user_id=uid, role=ParticipantRole.TRAINER)
                    )

            for uid in new_trainees_set:
                if uid in existing_participants_map:
                    p = existing_participants_map[uid]
                    p.role = ParticipantRole.TRAINEE
                    new_participants.append(p)
                else:
                    new_participants.append(
                        MeetingParticipant(user_id=uid, role=ParticipantRole.TRAINEE)
                    )

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
