from datetime import datetime, timedelta, timezone
from typing import cast

from fastapi import UploadFile

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.events import ParticipantCheckedIn
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.datetime_types import parse_datetime_to_utc
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.shared.infrastructure.minio_service import MinioService


def parse_client_time_to_utc(client_time: str) -> datetime:
    """Chuyển client_time (ISO string) thành datetime UTC aware."""
    try:
        return parse_datetime_to_utc(client_time)
    except Exception as err:
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
        now = datetime.now(timezone.utc)

        check_in_dt = now
        if client_time:
            check_in_dt = parse_client_time_to_utc(client_time)

        file_content = await image.read()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"meetings/checkin_bulk_{timestamp}_{image.filename}"

        image_url = await self.minio_service.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=image.content_type or "image/jpeg",
        )

        half_hour = timedelta(minutes=30)
        window_start = check_in_dt - half_hour
        window_end = check_in_dt + half_hour

        updated_participants = []
        messages = []

        for user_id in user_ids:
            participations = (
                self.participant_repo.find_all_participations_in_time_window(
                    user_id, window_start, window_end, check_in_dt
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

                if (
                    client_event_id
                    and participant.client_event_id == client_event_id
                ):
                    messages.append(
                        f"Yêu cầu trùng lặp (client_event_id), đã bỏ qua cho '{meeting.title}'"
                    )
                    continue

                # Ủy quyền 100% quy tắc nghiệp vụ kiểm tra trạng thái và mốc thời gian cho Domain Entity
                success, msg, is_late = participant.record_check_in(
                    check_in_time=check_in_dt,
                    meeting_start_time=meeting.start_time,
                    image_url=image_url,
                    client_event_id=client_event_id,
                )
                if not success:
                    messages.append(msg)
                    updated_participants.append(participant)
                    continue

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
                            check_in_at=saved_p.check_in_at or check_in_dt,
                            is_late=is_late,
                            meeting_title=meeting.title,
                        ),
                    )
                )

        return updated_participants, ". ".join(messages)
