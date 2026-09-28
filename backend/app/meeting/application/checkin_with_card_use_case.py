from datetime import timedelta
from typing import cast

from loguru import logger

from app.meeting.domain.events import ParticipantCheckedIn
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.infrastructure.tts_service import TTSService
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


class CheckInWithCardUseCase:
    """Check-in mã thẻ: tìm user → meeting và trả về audio giọng nói."""

    def __init__(
        self,
        user_repo: UserRepository,
        participant_repo: ParticipantRepository,
        meeting_repo: MeetingRepository,
        tts_service: TTSService,
        event_bus: type[EventBus] = EventBus,
    ):
        self.user_repo = user_repo
        self.participant_repo = participant_repo
        self.meeting_repo = meeting_repo
        self.tts_service = tts_service
        self.event_bus = event_bus

    async def execute(self, card_code: str) -> tuple[str, bytes]:
        """
        Thực hiện điểm danh và tổng hợp giọng nói TTS trả về audio bytes.

        Returns:
            tuple[str, bytes]: (Thông báo dạng chữ, Dữ liệu audio WAV)
        """
        code = (card_code or "").strip()
        if not code:
            msg = "Mã thẻ không hợp lệ"
            audio = await self._synthesize_message(msg)
            return msg, audio

        user = self.user_repo.get_by_check_in_card_code(code)
        if not user:
            msg = "Thẻ chưa được đăng ký trong hệ thống"
            audio = await self._synthesize_message(msg)
            return msg, audio

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
            msg = (
                f"Xin chào {user.name}, hiện tại bạn không có buổi họp nào "
                f"trong vòng 30 phút"
            )
            audio = await self._synthesize_message(msg)
            return msg, audio

        meeting = self.meeting_repo.get_domain_for_check_in(
            participant.meeting_id
        )
        if not meeting:
            msg = f"Xin chào {user.name}, không tìm thấy thông tin buổi họp"
            audio = await self._synthesize_message(msg)
            return msg, audio

        if participant.status in (
            ParticipantStatus.JOINED,
            ParticipantStatus.COMPLETED,
        ):
            msg = (
                f"Xin chào {user.name}, bạn đã điểm danh cho buổi họp "
                f"{meeting.title} rồi"
            )
            audio = await self._synthesize_message(msg)
            return msg, audio

        success, err_msg = participant.check_in(
            now, None, status=ParticipantStatus.JOINED
        )
        if not success:
            msg = f"Xin chào {user.name}, {err_msg}"
            audio = await self._synthesize_message(msg)
            return msg, audio

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

        msg = (
            f"Xin chào {user.name}, bạn đã điểm danh thành công cho "
            f"buổi họp {meeting.title}"
        )
        audio = await self._synthesize_message(msg)
        return msg, audio

    async def _synthesize_message(self, text: str) -> bytes:
        """Helper chuyển câu thông báo sang audio bytes sử dụng TTSService."""
        try:
            return await self.tts_service.synthesize(text=text)
        except Exception as exc:
            logger.error(
                f"Failed to synthesize speech for message '{text}': {exc}"
            )
            return b""
