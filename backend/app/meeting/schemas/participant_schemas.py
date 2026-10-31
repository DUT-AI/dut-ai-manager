from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.meeting.domain.value_objects import ParticipantStatus
from app.shared.domain.datetime_types import UtcDateTime


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
    user_name: str
    user_avatar_url: str | None = None
    check_in_at: UtcDateTime | None = None
    check_out_at: UtcDateTime | None = None
    status: ParticipantStatus
    link_image: str | None = None

    @model_validator(mode="before")
    @classmethod
    def map_user_info(cls, data: Any) -> Any:
        """Tự động lấy user_name và user_avatar từ đối tượng user nếu có."""
        if isinstance(data, dict):
            user = data.get("user")
            if user and isinstance(user, dict):
                if not data.get("user_name"):
                    data["user_name"] = user.get("name")
                if not data.get("user_avatar_url"):
                    data["user_avatar_url"] = user.get("avatar_url")
        else:
            # Nếu là object (Domain Entity hoặc ORM)
            user = getattr(data, "user", None)
            if user:
                if not getattr(data, "user_name", None):
                    d = {
                        "id": getattr(data, "id", None),
                        "user_id": getattr(data, "user_id", None),
                        "user_name": getattr(user, "name", ""),
                        "user_avatar_url": getattr(user, "avatar_url", None),
                        "check_in_at": getattr(data, "check_in_at", None),
                        "check_out_at": getattr(data, "check_out_at", None),
                        "status": getattr(data, "status", None),
                        "link_image": getattr(data, "link_image", None),
                    }
                    return d
        return data

    @classmethod
    def from_domain(cls, p: Any) -> "ParticipantResponse":
        if getattr(p, "id", None) is None:
            raise ValueError("Participant thiếu id")
        p_user = getattr(p, "user", None)
        user_name = getattr(p_user, "name", None) or f"User #{p.user_id}"
        user_avatar = getattr(p_user, "avatar_url", None)
        return cls(
            id=p.id,
            user_id=p.user_id,
            user_name=user_name,
            user_avatar_url=user_avatar,
            check_in_at=p.check_in_at,
            check_out_at=p.check_out_at,
            status=p.status,
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
