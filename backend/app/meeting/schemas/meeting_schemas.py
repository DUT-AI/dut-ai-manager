from datetime import UTC, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from app.meeting.domain.value_objects import ParticipantRole, ParticipantStatus
from app.shared.domain.datetime_types import UtcDateTime

from .participant_schemas import ParticipantResponse

if TYPE_CHECKING:
    from app.meeting.domain.meeting import Meeting as DomainMeeting


class UserRefDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    avatar_url: str | None = None


class MeetingCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str | None = Field(None, max_length=1000)
    start_time: UtcDateTime
    end_time: UtcDateTime
    require_check_in: bool = True
    enable_evaluation: bool = False
    trainer_ids: list[int] = Field(
        default_factory=list, description="Danh sách ID Trainer"
    )
    trainee_ids: list[int] = Field(
        default_factory=list, description="Danh sách ID Trainee"
    )


class MeetingUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = Field(None, max_length=1000)
    start_time: UtcDateTime | None = None
    end_time: UtcDateTime | None = None
    require_check_in: bool | None = None
    enable_evaluation: bool | None = None
    trainer_ids: list[int] | None = None
    trainee_ids: list[int] | None = None


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str | None = None
    start_time: datetime
    end_time: datetime
    require_check_in: bool
    enable_evaluation: bool = False
    evaluation_deadline: datetime | None = None
    created_by: int | None = None
    trainers: list[UserRefDto] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, m: "DomainMeeting") -> "MeetingResponse":
        """Map domain Meeting → schema (metadata only)."""
        if m.id is None or m.created_at is None or m.updated_at is None:
            raise ValueError("Meeting thiếu id hoặc timestamps sau khi lưu")

        trainers_dto: list[UserRefDto] = []
        for t in m.trainers:
            if t.user is not None:
                trainers_dto.append(
                    UserRefDto(
                        id=t.user.id,
                        name=t.user.name or f"Trainer #{t.user.id}",
                        avatar_url=t.user.avatar_url,
                    )
                )
            else:
                trainers_dto.append(
                    UserRefDto(
                        id=t.user_id,
                        name=f"Trainer #{t.user_id}",
                        avatar_url=None,
                    )
                )

        return cls(
            id=m.id,
            title=m.title,
            content=m.content,
            start_time=m.start_time,
            end_time=m.end_time,
            require_check_in=m.require_check_in,
            enable_evaluation=m.enable_evaluation
            if m.enable_evaluation is not None
            else False,
            evaluation_deadline=m.evaluation_deadline,
            created_by=m.created_by,
            trainers=trainers_dto,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class MeetingDetailResponse(BaseModel):
    """Schema chi tiết của Meeting phân tách thành 2 danh sách trainers và trainees."""

    id: int
    title: str
    content: str | None = None
    start_time: datetime
    end_time: datetime
    require_check_in: bool
    enable_evaluation: bool = False
    evaluation_deadline: datetime | None = None
    created_by: int | None = None
    trainers: list[ParticipantResponse] = Field(default_factory=list)
    trainees: list[ParticipantResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, m: "DomainMeeting") -> "MeetingDetailResponse":
        """Map domain Meeting → detail schema (phân chia trainers và trainees rõ ràng)."""
        now = datetime.now(UTC)
        end_time_utc = (
            m.end_time
            if m.end_time.tzinfo is not None
            else m.end_time.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")).astimezone(UTC)
        )
        is_ended = now > end_time_utc

        trainers: list[ParticipantResponse] = []
        trainees: list[ParticipantResponse] = []

        for p in m.participants:
            if p.is_deleted or p.id is None:
                continue

            check_out_at = p.check_out_at
            status = p.status

            # Auto-set checkout if meeting ended and participant not checked out
            if is_ended:
                if p.check_in_at and not check_out_at:
                    check_out_at = m.end_time
                    if status in (
                        ParticipantStatus.JOINED,
                        ParticipantStatus.LATE_EXCUSED,
                        ParticipantStatus.LATE_UNEXCUSED,
                    ):
                        status = ParticipantStatus.COMPLETED
                elif not p.check_in_at and status == ParticipantStatus.NOT_JOINED:
                    status = ParticipantStatus.ABSENT_UNEXCUSED

            # Read user from snapshot or fallback cleanly
            p_user = p.user
            user_name = p_user.name if p_user and p_user.name else f"User #{p.user_id}"
            user_avatar = p_user.avatar_url if p_user else None

            p_dto = ParticipantResponse(
                id=p.id,
                user_id=p.user_id,
                role=p.role,
                user_name=user_name,
                user_avatar_url=user_avatar,
                check_in_at=p.check_in_at,
                check_out_at=check_out_at,
                status=status,
                link_image=p.link_image,
            )

            if p.role == ParticipantRole.TRAINER:
                trainers.append(p_dto)
            else:
                trainees.append(p_dto)

        return cls(
            id=m.id,
            title=m.title,
            content=m.content,
            start_time=m.start_time,
            end_time=m.end_time,
            require_check_in=m.require_check_in,
            enable_evaluation=m.enable_evaluation
            if m.enable_evaluation is not None
            else False,
            evaluation_deadline=m.evaluation_deadline,
            created_by=m.created_by,
            trainers=trainers,
            trainees=trainees,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class MeetingSeatAvailabilityDto(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    max_seats: int
    occupied_seats: int
    available_seats: int
    is_full: bool

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "MeetingCreate",
    "MeetingDetailResponse",
    "MeetingResponse",
    "MeetingSeatAvailabilityDto",
    "MeetingUpdate",
    "UserRefDto",
]
