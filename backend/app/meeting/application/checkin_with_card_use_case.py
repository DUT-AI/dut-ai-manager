from datetime import datetime, timedelta, timezone
from typing import cast

from loguru import logger

from app.meeting.domain.events import ParticipantCheckedIn
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.infrastructure.audio_utils import downsample_wav_to_16k_mono
from app.shared.infrastructure.minio_service import MinioService
from app.shared.infrastructure.tts_service import TTSService
from app.user.infrastructure.repository import UserRepository


class CheckInWithCardUseCase:
    """Check-in mã thẻ: tìm user → meeting và trả về audio giọng nói (có cache MinIO)."""

    def __init__(
        self,
        user_repo: UserRepository,
        participant_repo: ParticipantRepository,
        meeting_repo: MeetingRepository,
        tts_service: TTSService,
        minio_service: MinioService,
        event_bus: type[EventBus] = EventBus,
    ):
        self.user_repo = user_repo
        self.participant_repo = participant_repo
        self.meeting_repo = meeting_repo
        self.tts_service = tts_service
        self.minio_service = minio_service
        self.event_bus = event_bus

    async def execute(self, card_code: str) -> tuple[str, bytes]:
        """
        Thực hiện điểm danh và tổng hợp giọng nói TTS (hoặc lấy từ cache MinIO).

        Returns:
            tuple[str, bytes]: (Thông báo dạng chữ, Dữ liệu audio WAV)
        """
        version_cache = f"{8}"
        code = (card_code or "").strip()
        if not code:
            msg = "Mã thẻ không hợp lệ"
            audio = await self._synthesize_message(
                msg, cache_key="tts/system/invalid_card.wav"
            )
            return msg, audio

        # 1. Lấy thông tin user tóm tắt (chỉ id, name, code) để tránh N+1 Role/Permission
        user = self.user_repo.get_summary_by_card_code(code)
        if not user:
            msg = f"{code}"
            audio = await self._synthesize_message(
                "Hãy đăng ký thẻ trên hệ thống với code hiển thị ở màn hình", cache_key=f"tts/system/card_not_registered_v{version_cache}.wav"
            )
            return msg, audio

        uid = user.id
        assert uid is not None

        now = datetime.now(timezone.utc)
        half_hour = timedelta(minutes=30)
        window_start = now - half_hour
        window_end = now + half_hour

        # 2. Tìm participant kèm meeting đã được JOIN sẵn (không cần query lại bảng meetings)
        participant = self.participant_repo.find_participation_in_time_window(
            uid, window_start, window_end, now
        )
        if not participant or participant.meeting_id is None:
            msg = "không có buổi họp nào trong vòng 30 phút"
            
            text_to_speech = (
                f"Xin chào {user.name}, hiện tại bạn không có buổi họp nào "
                f"trong vòng 30 phút"
            )
            audio = await self._synthesize_message(
                text_to_speech, cache_key=f"tts/users/user_{uid}_no_meeting_v{version_cache}.wav"
            )
            return msg, audio

        meeting = self.meeting_repo.get_domain_for_check_in(participant.meeting_id)
        if not meeting:
            msg = "không tìm thấy thông tin buổi họp"
            text_to_speech = f"Xin chào {user.name}, không tìm thấy thông tin buổi họp"
            audio = await self._synthesize_message(
                text_to_speech, cache_key=f"tts/users/user_{uid}_no_meeting_v{version_cache}.wav"
            )
            return msg, audio

        if participant.status == ParticipantStatus.COMPLETED or (
            participant.status in (ParticipantStatus.JOINED, ParticipantStatus.LATE_UNEXCUSED)
            and participant.check_in_at is not None
        ):
            msg = "bạn đã điểm danh cho buổi họp rồi"
            text_to_speech = (
                f"Xin chào {user.name}, bạn đã điểm danh cho buổi họp rồi"
            )
            audio = await self._synthesize_message(
                text_to_speech,
                cache_key=f"tts/users/user_{uid}_already_checked_in_v{version_cache}.wav"
            )
            return msg, audio

        success, err_msg, is_late = participant.record_check_in(
            check_in_time=now,
            meeting_start_time=meeting.start_time,
        )
        if not success:
            msg = f"Xin chào {user.name}, {err_msg}"
            audio = await self._synthesize_message(msg)
            return msg, audio

        self.participant_repo.save(participant)
        await self.event_bus.publish(
            cast(
                DomainEvent,
                ParticipantCheckedIn(
                    meeting_id=participant.meeting_id,
                    user_id=uid,
                    check_in_at=participant.check_in_at or now,
                    is_late=is_late,
                    meeting_title=meeting.title,
                ),
            )
        )

        # Lời chào check-in thành công cho từng người (Cache trên MinIO theo user_id)
        msg = "bạn đã điểm danh thành công"
        text_to_speech = f"Xin chào {user.name}, bạn đã điểm danh thành công"
        user_cache_key = f"tts/users/user_{uid}_checkin_v{version_cache}.wav"
        audio = await self._synthesize_message(text_to_speech, cache_key=user_cache_key)
        return msg, audio

    async def _synthesize_message(
        self, text: str, cache_key: str | None = None
    ) -> bytes:
        """Helper chuyển câu thông báo sang audio bytes sử dụng cache MinIO."""
        try:
            if cache_key:
                audio_bytes = await self.tts_service.synthesize_with_cache(
                    text=text,
                    cache_key=cache_key,
                    minio_service=self.minio_service,
                )
                if audio_bytes:
                    audio_bytes = downsample_wav_to_16k_mono(
                        audio_bytes, target_rate=11025, target_bits=8, speed=1.25
                    )
                return audio_bytes
            raw_audio = await self.tts_service.synthesize(text=text)
            if raw_audio:
                return downsample_wav_to_16k_mono(
                    raw_audio, target_rate=11025, target_bits=8, speed=1.25
                )
            return raw_audio
        except Exception as exc:
            logger.error(f"Failed to synthesize speech for message '{text}': {exc}")
            return b""
