from datetime import datetime, timedelta, timezone
from typing import cast

from fastapi import UploadFile

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.events import ParticipantCheckedIn
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.infrastructure.minio_service import MinioService
from app.utils.datetime import get_current_utc7_time


def parse_client_time_to_utc7_naive(client_time: str) -> datetime:
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
            check_in_dt = parse_client_time_to_utc7_naive(client_time)

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
