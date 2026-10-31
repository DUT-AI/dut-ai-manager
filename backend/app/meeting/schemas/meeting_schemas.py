from datetime import UTC, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from app.meeting.domain.value_objects import ParticipantStatus
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
    user_ids: list[int] = []


class MeetingUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = Field(None, max_length=1000)
    start_time: UtcDateTime | None = None
    end_time: UtcDateTime | None = None
    require_check_in: bool | None = None
    enable_evaluation: bool | None = None
    user_ids: list[int] | None = None


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
    trainer: UserRefDto | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, m: "DomainMeeting") -> "MeetingResponse":
        """Map domain Meeting → schema (metadata only)."""
        if m.id is None or m.created_at is None or m.updated_at is None:
            raise ValueError("Meeting thiếu id hoặc timestamps sau khi lưu")

        # Enforce Trainer Contract & Read profile from ORM relation if present
        trainer_dto: UserRefDto | None = None
        creator_rel = getattr(m, "creator", None)
        if creator_rel and getattr(creator_rel, "id", None):
            trainer_dto = UserRefDto(
                id=creator_rel.id,
                name=creator_rel.name or f"Trainer #{creator_rel.id}",
                avatar_url=creator_rel.avatar_url,
            )
        elif m.created_by:
            trainer_dto = UserRefDto(
                id=m.created_by,
                name=f"Trainer #{m.created_by}",
                avatar_url=None,
            )
        else:
            trainer_dto = UserRefDto(
                id=0,
                name="Unknown Trainer",
                avatar_url=None,
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
            trainer=trainer_dto,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class MeetingDetailResponse(MeetingResponse):
    """Schema chi tiết của Meeting bao gồm danh sách người tham gia."""

    participants: list[ParticipantResponse] = []

    @classmethod
    def from_domain(cls, m: "DomainMeeting") -> "MeetingDetailResponse":
        """Map domain Meeting → detail schema (kèm participants)."""
        base_res = MeetingResponse.from_domain(m)
        now = datetime.now(UTC)
        end_time_utc = (
            m.end_time
            if m.end_time.tzinfo is not None
            else m.end_time.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")).astimezone(UTC)
        )
        is_ended = now > end_time_utc

        participants_raw = getattr(m, "participants", []) or []
        participants: list[ParticipantResponse] = []
        for p in participants_raw:
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

            if p.id is None:
                continue

            # Read user from ORM relationship or fallback cleanly
            p_user = getattr(p, "user", None)
            user_name = getattr(p_user, "name", None) or f"User #{p.user_id}"
            user_avatar = getattr(p_user, "avatar_url", None)

            participants.append(
                ParticipantResponse(
                    id=p.id,
                    user_id=p.user_id,
                    user_name=user_name,
                    user_avatar_url=user_avatar,
                    check_in_at=p.check_in_at,
                    check_out_at=check_out_at,
                    status=status,
                    link_image=p.link_image,
                )
            )

        return cls(
            **base_res.model_dump(),
            participants=participants,
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
