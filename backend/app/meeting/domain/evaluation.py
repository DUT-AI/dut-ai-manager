from pydantic import BaseModel, Field

from app.meeting.domain.value_objects import (
    EvaluationCriteria,
    EvaluationCriteriaCode,
    EvaluationCriterion,
    EvaluationType,
    UserRef,
)
from app.shared.domain.base_entity import BaseEntity


class EvaluationScoreItem(BaseModel):
    """Điểm của từng tiêu chí đánh giá (Value Object)"""

    criteria_code: str
    score: int = Field(ge=1, le=5)


class MeetingOverallEvaluation(BaseEntity):
    """Phiếu đánh giá tổng thể buổi học từ Trainer (Quan hệ 1-1 với Meeting)."""

    meeting_id: int
    trainer_id: int
    scores: list[EvaluationScoreItem] = Field(default_factory=list)
    average_score: float = 0.0
    general_feedback: str | None = None
    trainer: UserRef | None = None

    def calculate_average(self) -> float:
        """Tính điểm trung bình cộng của các tiêu chí đánh giá buổi học."""
        if not self.scores:
            self.average_score = 0.0
            return 0.0
        self.average_score = round(
            sum(s.score for s in self.scores) / len(self.scores), 2
        )
        return self.average_score


class MeetingEvaluation(BaseEntity):
    """Phiếu đánh giá cá nhân 2 chiều giữa Trainer và Trainee (Domain Entity)"""

    meeting_id: int
    reviewer_id: int
    target_user_id: int
    evaluation_type: EvaluationType
    is_anonymous: bool = False
    scores: list[EvaluationScoreItem] = Field(default_factory=list)
    average_score: float = 0.0
    feedback_text: str | None = None
    reviewer: UserRef | None = None
    target_user: UserRef | None = None

    def calculate_average(self) -> float:
        """Tính điểm trung bình cộng của các tiêu chí."""
        if not self.scores:
            self.average_score = 0.0
            return 0.0
        self.average_score = round(
            sum(s.score for s in self.scores) / len(self.scores), 2
        )
        return self.average_score


EvaluationScoreItem.model_rebuild()
MeetingOverallEvaluation.model_rebuild()
MeetingEvaluation.model_rebuild()

__all__ = [
    "EvaluationCriteria",
    "EvaluationCriteriaCode",
    "EvaluationCriterion",
    "EvaluationScoreItem",
    "MeetingEvaluation",
    "MeetingOverallEvaluation",
]
