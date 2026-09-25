from datetime import timedelta
from typing import cast

from app.meeting.domain.events import ParticipantCheckedIn
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


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
        assert uid is not None

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

        success, msg = participant.check_in(now, None, status=ParticipantStatus.JOINED)
        if not success:
            raise BadRequestException(msg)

        self.participant_repo.save(participant)
        is_late = meeting.is_late(now)
        assert uid is not None
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
