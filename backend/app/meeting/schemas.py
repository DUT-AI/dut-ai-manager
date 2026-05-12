from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Any

from pydantic import BaseModel, Field, ConfigDict, model_validator

from .domain.value_objects import ParticipantStatus

if TYPE_CHECKING:
    from app.meeting.domain.entity import Meeting as DomainMeeting
    from app.meeting.domain.entity import MeetingParticipant as DomainParticipant


class CheckInWithCardRequest(BaseModel):
    """Body check-in quẹt thẻ tại quầy (không cần đăng nhập)."""

    card_code: str = Field(..., min_length=1, description="Mã thẻ check-in")

class CheckOutRequest(BaseModel):
    user_id: int = Field(..., description="ID của user cần check-out")


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    check_in_at: Optional[datetime] = None
    status: ParticipantStatus
    link_image: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_user_info(cls, data: Any) -> Any:
        """Tự động lấy user_name và user_avatar từ đối tượng user nếu có."""
        if isinstance(data, dict):
            user = data.get("user")
            if user and isinstance(user, dict):
                if not data.get("user_name"):
                    data["user_name"] = user.get("name")
                if not data.get("user_avatar"):
                    data["user_avatar"] = user.get("avatar_url")
        else:
            # Nếu là object (Domain Entity hoặc ORM)
            user = getattr(data, "user", None)
            if user:
                if not getattr(data, "user_name", None):
                    # Chúng ta trả về dict mới để không mutate object gốc
                    d = {
                        "id": getattr(data, "id", None),
                        "user_id": getattr(data, "user_id", None),
                        "user_name": getattr(user, "name", ""),
                        "user_avatar": getattr(user, "avatar_url", None),
                        "check_in_at": getattr(data, "check_in_at", None),
                        "status": getattr(data, "status", None),
                        "link_image": getattr(data, "link_image", None),
                    }
                    return d
        return data

    @classmethod
    def from_domain(cls, p: "DomainParticipant") -> "ParticipantResponse":
        if p.id is None:
            raise ValueError("Participant thiếu id")
        return cls(
            id=p.id,
            user_id=p.user_id,
            user_name=p.user.name if p.user else "",
            user_avatar=p.user.avatar_url if p.user else None,
            check_in_at=p.check_in_at,
            status=p.status,
            link_image=p.link_image,
        )


class MeetingCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: Optional[str] = Field(None, max_length=1000)
    start_time: datetime
    end_time: datetime
    require_check_in: bool = True
    user_ids: List[int] = []
    team_ids: List[int] = []


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, max_length=1000)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    require_check_in: Optional[bool] = None
    user_ids: Optional[List[int]] = None
    team_ids: Optional[List[int]] = None


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: Optional[str]
    start_time: datetime
    end_time: datetime
    require_check_in: bool
    participants: List[ParticipantResponse] = []
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, m: "DomainMeeting") -> "MeetingResponse":
        """Map domain Meeting → schema (user_name, timestamps, participant id)."""
        if m.id is None or m.created_at is None or m.updated_at is None:
            raise ValueError("Meeting thiếu id hoặc timestamps sau khi lưu")
        participants: List[ParticipantResponse] = []
        for p in m.participants:
            participants.append(ParticipantResponse.from_domain(p))
        return cls(
            id=m.id,
            title=m.title,
            content=m.content,
            start_time=m.start_time,
            end_time=m.end_time,
            require_check_in=m.require_check_in,
            participants=participants,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
