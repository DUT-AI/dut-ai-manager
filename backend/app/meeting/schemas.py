from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.utils.datetime import get_current_utc7_time

from .domain.value_objects import (
    CriteriaBreakdownSummary,
    EvaluationCriterion,
    ParticipantStatus,
)

if TYPE_CHECKING:
    from app.meeting.domain.entity import Meeting as DomainMeeting


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
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
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
                    # Chúng ta trả về dict mới để không mutate object gốc
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
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None


class UserRefDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    avatar_url: str | None = None


class MeetingCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str | None = Field(None, max_length=1000)
    start_time: datetime
    end_time: datetime
    require_check_in: bool = True
    enable_evaluation: bool = False
    user_ids: list[int] = []


class MeetingUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = Field(None, max_length=1000)
    start_time: datetime | None = None
    end_time: datetime | None = None
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
        now = get_current_utc7_time()
        is_ended = now > m.end_time

        participants_raw = getattr(m, "participants", []) or []
        participants: list[ParticipantResponse] = []
        for p in participants_raw:
            check_out_at = p.check_out_at
            status = p.status

            # Auto-set checkout time and status if meeting ended & checked in but not checked out
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


# ==========================================
# EVALUATION SCHEMAS
# ==========================================


class EvaluationScoreItemDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    criteria_code: str = Field(..., description="Mã tiêu chí đánh giá")
    criteria_name: str = Field(
        ..., description="Tên hiển thị của tiêu chí (Bắt buộc, không được null)"
    )
    criteria_description: str = Field(
        ..., description="Mô tả chi tiết của tiêu chí (Bắt buộc, không được null)"
    )
    score: int = Field(..., ge=1, le=5, description="Điểm đánh giá từ 1 đến 5 sao")


class EvaluationScoreItemSubmitDto(BaseModel):
    """DTO cho request submit đánh giá từ client (chỉ cần mã tiêu chí và điểm)"""

    model_config = ConfigDict(from_attributes=True)

    criteria_code: str = Field(..., description="Mã tiêu chí đánh giá")
    score: int = Field(..., ge=1, le=5, description="Điểm đánh giá từ 1 đến 5 sao")


class TrainerSubmitEvaluationRequest(BaseModel):
    target_user_id: int = Field(..., description="ID của Trainee nhận đánh giá")
    scores: list[EvaluationScoreItemSubmitDto] = Field(
        ..., min_length=1, description="Danh sách điểm tiêu chí"
    )
    feedback_text: str | None = Field(
        None, max_length=2000, description="Nhận xét chi tiết"
    )


class TraineeSubmitEvaluationRequest(BaseModel):
    target_user_id: int | None = Field(
        None,
        description="ID của Trainer nhận đánh giá (tự động lấy người tạo buổi học nếu bỏ trống)",
    )
    is_anonymous: bool = Field(
        False, description="Tùy chọn gửi ẩn danh (không hiện tên với Trainer)"
    )
    scores: list[EvaluationScoreItemSubmitDto] = Field(
        ..., min_length=1, description="Danh sách điểm tiêu chí"
    )
    feedback_text: str | None = Field(
        None, max_length=2000, description="Góp ý cho Trainer"
    )


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    reviewer_id: int | None = None
    target_user_id: int
    evaluation_type: str
    is_anonymous: bool = False
    scores: list[EvaluationScoreItemDto]
    average_score: float
    feedback_text: str | None = None
    reviewer: UserRefDto | None = None
    target_user: UserRefDto | None = None
    created_at: datetime

    @classmethod
    def from_domain(cls, e: Any) -> "EvaluationResponse":
        scores_dtos = []
        for s in getattr(e, "scores", []) or []:
            code = getattr(s, "criteria_code", "")
            criterion = EvaluationCriterion.from_code(code)
            scores_dtos.append(
                EvaluationScoreItemDto(
                    criteria_code=code,
                    criteria_name=criterion.name,
                    criteria_description=criterion.description,
                    score=getattr(s, "score", 0),
                )
            )
        reviewer_dto = None
        if not getattr(e, "is_anonymous", False) and getattr(e, "reviewer", None):
            rev = e.reviewer
            reviewer_dto = UserRefDto(
                id=getattr(rev, "id", 0),
                name=getattr(rev, "name", ""),
                avatar_url=getattr(rev, "avatar_url", None),
            )
        target_dto = None
        if getattr(e, "target_user", None):
            tgt = e.target_user
            target_dto = UserRefDto(
                id=getattr(tgt, "id", 0),
                name=getattr(tgt, "name", ""),
                avatar_url=getattr(tgt, "avatar_url", None),
            )

        eval_type = getattr(e, "evaluation_type", "")
        if hasattr(eval_type, "value"):
            eval_type = eval_type.value

        return cls(
            id=getattr(e, "id", 0) or 0,
            meeting_id=e.meeting_id,
            reviewer_id=None
            if getattr(e, "is_anonymous", False)
            else getattr(e, "reviewer_id", None),
            target_user_id=e.target_user_id,
            evaluation_type=str(eval_type),
            is_anonymous=getattr(e, "is_anonymous", False),
            scores=scores_dtos,
            average_score=getattr(e, "average_score", 0.0),
            feedback_text=getattr(e, "feedback_text", None),
            reviewer=reviewer_dto,
            target_user=target_dto,
            created_at=getattr(e, "created_at", None) or datetime.now(),
        )


class CriteriaAverageScoreDto(BaseModel):
    criteria_code: str
    criteria_name: str
    criteria_description: str
    average_score: float
    count: int
    evaluation_type: str | None = None

    @classmethod
    def from_summary(cls, summary: CriteriaBreakdownSummary) -> "CriteriaAverageScoreDto":
        """Khởi tạo DTO trực tiếp từ Domain Value Object CriteriaBreakdownSummary."""
        etype = summary.evaluation_type
        etype_str = etype.value if hasattr(etype, "value") else str(etype)
        return cls(
            criteria_code=summary.criteria_code,
            criteria_name=summary.criteria_name,
            criteria_description=summary.criteria_description,
            average_score=summary.average_score,
            count=summary.count,
            evaluation_type=etype_str,
        )


class MeetingEvaluationSummaryResponse(BaseModel):
    meeting_id: int
    total_evaluations: int
    overall_average_score: float
    criteria_breakdown: list[CriteriaAverageScoreDto]
    evaluations: list[EvaluationResponse]
    total_trainer_evaluations: int = 0
    total_trainee_evaluations: int = 0
    trainer_average_score: float | None = None
    trainee_average_score: float | None = None


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


