from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from app.meeting.domain.value_objects import ParticipantRole
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

        trainers_dto: list[UserRefDto] = [
            UserRefDto(
                id=t.user.id if t.user else t.user_id,
                name=t.user.name if t.user else "",
                avatar_url=t.user.avatar_url if t.user else None,
            )
            for t in m.trainers
        ]

        return cls(
            id=m.id,
            title=m.title,
            content=m.content,
            start_time=m.start_time,
            end_time=m.end_time,
            require_check_in=m.require_check_in,
            enable_evaluation=m.enable_evaluation,
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
        """Map domain Meeting → detail schema (trainers và trainees)."""
        trainers: list[ParticipantResponse] = []
        trainees: list[ParticipantResponse] = []

        for p in m.participants:
            if p.id is None:
                continue

            p_dto = ParticipantResponse.from_domain(p)
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
            enable_evaluation=m.enable_evaluation,
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
