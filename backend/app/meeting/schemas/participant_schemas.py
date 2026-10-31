from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from app.meeting.domain.value_objects import ParticipantRole, ParticipantStatus
from app.shared.domain.datetime_types import UtcDateTime

if TYPE_CHECKING:
    from app.meeting.domain.participant import MeetingParticipant


class CheckInWithCardRequest(BaseModel):
    """Body check-in quẹt thẻ tại quầy (không cần đăng nhập)."""

    card_code: str = Field(..., min_length=1, description="Mã thẻ check-in")


class CheckOutRequest(BaseModel):
    user_id: int = Field(..., description="ID của user cần check-out")
    occurred_at: str | None = None
    check_out_at: str | None = None
    checkout_at: str | None = None
    check_out_time: str | None = None
    checkout_time: str | None = None
    timestamp: str | None = None
    client_time: str | None = None
    client_event_id: str | None = None
    event_id: str | None = None
    idempotency_key: str | None = None

    def get_client_time(self) -> str | None:
        return (
            self.occurred_at
            or self.check_out_at
            or self.checkout_at
            or self.check_out_time
            or self.checkout_time
            or self.timestamp
            or self.client_time
        )

    def get_idempotency_key(self) -> str | None:
        return self.client_event_id or self.event_id or self.idempotency_key


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: ParticipantRole = ParticipantRole.TRAINEE
    user_name: str
    user_avatar_url: str | None = None
    check_in_at: UtcDateTime | None = None
    check_out_at: UtcDateTime | None = None
    status: ParticipantStatus
    link_image: str | None = None

    @classmethod
    def from_domain(
        cls,
        p: "MeetingParticipant",
        *,
        override_status: ParticipantStatus | None = None,
        override_check_out_at: UtcDateTime | None = None,
    ) -> "ParticipantResponse":
        if p.id is None:
            raise ValueError("Participant thiếu id")

        user_name = p.user.name if p.user else ""
        user_avatar = p.user.avatar_url if p.user else None

        return cls(
            id=p.id,
            user_id=p.user_id,
            role=p.role,
            user_name=user_name,
            user_avatar_url=user_avatar,
            check_in_at=p.check_in_at,
            check_out_at=override_check_out_at or p.check_out_at,
            status=override_status or p.status,
            link_image=p.link_image,
        )


class UpdateParticipantStatusRequest(BaseModel):
    status: ParticipantStatus
    check_in_at: UtcDateTime | None = None
    check_out_at: UtcDateTime | None = None


__all__ = [
    "CheckInWithCardRequest",
    "CheckOutRequest",
    "ParticipantResponse",
    "UpdateParticipantStatusRequest",
]
