import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.meeting.application.checkin_with_card_use_case import (
    CheckInWithCardUseCase,
)
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.shared.infrastructure.tts_service import (
    DEFAULT_AUDIO_REPETITION_PENALTY,
    DEFAULT_AUDIO_TEMPERATURE,
    DEFAULT_AUDIO_TOPK,
    DEFAULT_AUDIO_TOPP,
    DEFAULT_CFG_SCALE,
    DEFAULT_MODEL,
    DEFAULT_NORMALIZE_TEXT,
    DEFAULT_RESPONSE_FORMAT,
    DEFAULT_SPEED,
    DEFAULT_VOICE,
    TTSService,
    TTSServiceError,
)
from app.user.domain.entity import UserEntity


def test_tts_service_payload_construction():
    service = TTSService()
    payload = service.build_payload("Xin chào")

    assert payload["input"] == "Xin chào"
    assert payload["model"] == DEFAULT_MODEL
    assert payload["voice"] == DEFAULT_VOICE
    assert payload["response_format"] == DEFAULT_RESPONSE_FORMAT
    assert payload["speed"] == DEFAULT_SPEED
    assert payload["normalize_text"] == DEFAULT_NORMALIZE_TEXT
    assert payload["cfg_scale"] == DEFAULT_CFG_SCALE
    assert payload["audio_temperature"] == DEFAULT_AUDIO_TEMPERATURE
    assert payload["audio_topk"] == DEFAULT_AUDIO_TOPK
    assert payload["audio_topp"] == DEFAULT_AUDIO_TOPP
    assert payload["audio_repetition_penalty"] == DEFAULT_AUDIO_REPETITION_PENALTY


def test_tts_service_empty_input_raises_error():
    service = TTSService()
    with pytest.raises(TTSServiceError) as exc_info:
        asyncio.run(service.synthesize(""))
    assert "cannot be empty" in str(exc_info.value)


def test_check_in_with_card_use_case_returns_speech_audio():
    user_repo = MagicMock()
    participant_repo = MagicMock()
    meeting_repo = MagicMock()
    tts_service = MagicMock()
    minio_service = MagicMock()
    tts_service.synthesize_with_cache = AsyncMock(return_value=b"RIFF_FAKE_AUDIO_BYTES")
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    user = UserEntity(id=1, name="Nguyễn Phước Nguyên", email="nguyen@example.com")
    user_repo.get_by_check_in_card_code.return_value = user

    now = datetime.now()
    meeting = Meeting(
        id=10,
        title="Họp DUT AI Team",
        start_time=now - timedelta(minutes=10),
        end_time=now + timedelta(minutes=50),
        require_check_in=True,
    )
    meeting_repo.get_domain_for_check_in.return_value = meeting

    participant = MeetingParticipant(
        id=100,
        meeting_id=10,
        user_id=1,
        status=ParticipantStatus.NOT_JOINED,
    )
    participant_repo.find_participation_in_time_window.return_value = participant
    participant_repo.save.return_value = participant

    use_case = CheckInWithCardUseCase(
        user_repo=user_repo,
        participant_repo=participant_repo,
        meeting_repo=meeting_repo,
        tts_service=tts_service,
        minio_service=minio_service,
        event_bus=event_bus,
    )

    msg, audio_bytes = asyncio.run(use_case.execute(card_code="CARD_123456"))

    assert "Nguyễn Phước Nguyên" in msg
    assert "thành công" in msg
    assert audio_bytes == b"RIFF_FAKE_AUDIO_BYTES"
    tts_service.synthesize_with_cache.assert_called_once()
    assert (
        tts_service.synthesize_with_cache.call_args.kwargs["cache_key"]
        == "tts/users/user_1_checkin.wav"
    )
    event_bus.publish.assert_called_once()


def test_tts_service_synthesize_with_cache_hit():
    service = TTSService()
    minio_mock = MagicMock()
    minio_mock.get_file_bytes = AsyncMock(return_value=b"CACHED_AUDIO_FROM_MINIO")
    service.synthesize = AsyncMock()

    result = asyncio.run(
        service.synthesize_with_cache(
            text="Xin chào",
            cache_key="tts/users/user_1_checkin.wav",
            minio_service=minio_mock,
        )
    )

    assert result == b"CACHED_AUDIO_FROM_MINIO"
    minio_mock.get_file_bytes.assert_called_once_with("tts/users/user_1_checkin.wav")
    service.synthesize.assert_not_called()


def test_tts_service_synthesize_with_cache_miss():
    service = TTSService()
    minio_mock = MagicMock()
    minio_mock.get_file_bytes = AsyncMock(return_value=None)
    minio_mock.upload_file = AsyncMock(return_value="https://minio/tts.wav")
    service.synthesize = AsyncMock(return_value=b"FRESH_GENERATED_TTS_BYTES")

    result = asyncio.run(
        service.synthesize_with_cache(
            text="Xin chào",
            cache_key="tts/users/user_1_checkin.wav",
            minio_service=minio_mock,
        )
    )

    assert result == b"FRESH_GENERATED_TTS_BYTES"
    minio_mock.get_file_bytes.assert_called_once_with("tts/users/user_1_checkin.wav")
    service.synthesize.assert_called_once_with("Xin chào")
    minio_mock.upload_file.assert_called_once()
