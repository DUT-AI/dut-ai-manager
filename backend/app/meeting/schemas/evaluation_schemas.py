from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.meeting.domain.value_objects import (
    CriteriaBreakdownSummary,
    EvaluationCriterion,
)

from .meeting_schemas import UserRefDto


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


class SubmitMeetingOverallEvaluationRequest(BaseModel):
    """Request DTO để Trainer gửi đánh giá tổng thể buổi học (quan hệ 1 - 1)"""

    scores: list[EvaluationScoreItemSubmitDto] = Field(
        ...,
        min_length=1,
        description="Danh sách điểm 4 tiêu chí chuẩn hóa của buổi học",
    )
    general_feedback: str | None = Field(
        None, max_length=2000, description="Nhận xét tổng thể về buổi học"
    )


class MeetingOverallEvaluationResponse(BaseModel):
    """Response DTO cho đánh giá tổng thể buổi học của Trainer"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    trainer_id: int
    scores: list[EvaluationScoreItemDto]
    average_score: float
    general_feedback: str | None = None
    trainer: UserRefDto | None = None
    created_at: datetime

    @classmethod
    def from_domain(cls, e: Any) -> "MeetingOverallEvaluationResponse":
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

        trainer_dto = None
        if getattr(e, "trainer", None):
            t = e.trainer
            trainer_dto = UserRefDto(
                id=getattr(t, "id", 0),
                name=getattr(t, "name", ""),
                avatar_url=getattr(t, "avatar_url", None),
            )

        return cls(
            id=getattr(e, "id", 0) or 0,
            meeting_id=e.meeting_id,
            trainer_id=e.trainer_id,
            scores=scores_dtos,
            average_score=getattr(e, "average_score", 0.0),
            general_feedback=getattr(e, "general_feedback", None),
            trainer=trainer_dto,
            created_at=getattr(e, "created_at", None) or datetime.now(UTC),
        )


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
        description="ID Trainer nhận đánh giá (mặc định người tạo buổi học)",
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
    def from_domain(
        cls, e: Any, current_user_id: int | None = None
    ) -> "EvaluationResponse":
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

        is_anon = getattr(e, "is_anonymous", False)
        actual_reviewer_id = getattr(e, "reviewer_id", None)
        is_owner = current_user_id is not None and actual_reviewer_id == current_user_id

        reviewer_dto = None
        if (not is_anon or is_owner) and getattr(e, "reviewer", None):
            rev = e.reviewer
            reviewer_dto = UserRefDto(
                id=getattr(rev, "id", 0),
                name=getattr(rev, "name", ""),
                avatar_url=getattr(rev, "avatar_url", None),
            )

        masked_reviewer_id = None if (is_anon and not is_owner) else actual_reviewer_id

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
            reviewer_id=masked_reviewer_id,
            target_user_id=e.target_user_id,
            evaluation_type=str(eval_type),
            is_anonymous=is_anon,
            scores=scores_dtos,
            average_score=getattr(e, "average_score", 0.0),
            feedback_text=getattr(e, "feedback_text", None),
            reviewer=reviewer_dto,
            target_user=target_dto,
            created_at=getattr(e, "created_at", None) or datetime.now(UTC),
        )


class CriteriaAverageScoreDto(BaseModel):
    criteria_code: str
    criteria_name: str
    criteria_description: str
    average_score: float
    count: int
    evaluation_type: str | None = None

    @classmethod
    def from_summary(
        cls, summary: CriteriaBreakdownSummary
    ) -> "CriteriaAverageScoreDto":
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
    my_evaluation: EvaluationResponse | None = None
    overall_evaluation: MeetingOverallEvaluationResponse | None = None


__all__ = [
    "CriteriaAverageScoreDto",
    "EvaluationResponse",
    "EvaluationScoreItemDto",
    "EvaluationScoreItemSubmitDto",
    "MeetingEvaluationSummaryResponse",
    "MeetingOverallEvaluationResponse",
    "SubmitMeetingOverallEvaluationRequest",
    "TraineeSubmitEvaluationRequest",
    "TrainerSubmitEvaluationRequest",
]
