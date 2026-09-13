"""
Meeting Check-In & Check-Out Use Cases — application layer.

Handles real-time check-in (API/Card) and check-out logic.
"""

from datetime import datetime, timedelta, timezone
from typing import cast

from fastapi import UploadFile

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.events import ParticipantCheckedIn, ParticipantCheckedOut
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.infrastructure.minio_service import MinioService
from app.user.infrastructure.repository import UserRepository
from app.utils.datetime import get_current_utc7_time


def _parse_client_time_to_utc7_naive(client_time: str) -> datetime:
    """Chuyển client_time (ISO string) thành datetime naive múi giờ UTC+7."""
    try:
        dt = datetime.fromisoformat(client_time.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            utc7_tz = timezone(timedelta(hours=7))
            dt = dt.astimezone(utc7_tz).replace(tzinfo=None)
        return dt
    except ValueError as err:
        raise BadRequestException("Invalid occurred_at") from err


class CheckInUseCase:
    """Thực hiện điểm danh cho thành viên tham gia buổi họp"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        minio_service: MinioService,
        event_bus: type[EventBus] = EventBus,
    ):
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo
        self.minio_service = minio_service
        self.event_bus = event_bus

    async def execute(
        self,
        user_ids: list[int],
        image: UploadFile,
        client_time: str | None = None,
        client_event_id: str | None = None,
    ) -> tuple[list[MeetingParticipant], str]:
        now = get_current_utc7_time()

        check_in_dt = now
        if client_time:
            check_in_dt = _parse_client_time_to_utc7_naive(client_time)

        file_content = await image.read()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"meetings/checkin_bulk_{timestamp}_{image.filename}"

        image_url = await self.minio_service.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=image.content_type or "image/jpeg",
        )

        half_hour = timedelta(minutes=30)
        window_start = now - half_hour
        window_end = now + half_hour

        updated_participants = []
        messages = []

        for user_id in user_ids:
            participations = (
                self.participant_repo.find_all_participations_in_time_window(
                    user_id, window_start, window_end, now
                )
            )

            if not participations:
                messages.append(
                    f"Người dùng {user_id} không có buổi họp nào trong khung thời gian này"
                )
                continue

            for participant in participations:
                meeting_id = participant.meeting_id
                if meeting_id is None:
                    continue

                meeting = self.meeting_repo.get_domain_for_check_in(meeting_id)
                if not meeting:
                    continue

                if participant.status in (
                    ParticipantStatus.JOINED,
                    ParticipantStatus.COMPLETED,
                ):
                    if (
                        client_event_id
                        and participant.client_event_id == client_event_id
                    ):
                        messages.append(
                            f"Yêu cầu trùng lặp (client_event_id), đã bỏ qua cho '{meeting.title}'"
                        )
                        continue
                    messages.append(
                        f"Người dùng {participant.user.name if participant.user else user_id} đã điểm danh cho '{meeting.title}'"
                    )
                    continue

                is_late = meeting.is_late(check_in_dt)
                success, msg = participant.check_in(check_in_dt, image_url, status=ParticipantStatus.JOINED)
                if not success:
                    messages.append(msg)
                    updated_participants.append(participant)
                    continue

                if client_event_id:
                    participant.client_event_id = client_event_id

                saved_p = self.participant_repo.save(participant)
                updated_participants.append(saved_p)
                messages.append(
                    f"Đã ghi nhận {participant.user.name if participant.user else user_id} cho '{meeting.title}'"
                )

                await self.event_bus.publish(
                    cast(
                        DomainEvent,
                        ParticipantCheckedIn(
                            meeting_id=meeting_id,
                            user_id=user_id,
                            check_in_at=check_in_dt,
                            is_late=is_late,
                            meeting_title=meeting.title,
                        ),
                    )
                )

        return updated_participants, ". ".join(messages)


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
            check_out_dt = _parse_client_time_to_utc7_naive(client_time)

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
