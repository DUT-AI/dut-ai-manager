from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel



class ParticipantStatus(str, Enum):
    """Trạng thái tham dự buổi họp (7 trạng thái)"""

    NOT_JOINED = "NOT_JOINED"  # Chưa checkin
    JOINED = "JOINED"  # Đã checkin (đúng/trước giờ)
    LATE_EXCUSED = "LATE_EXCUSED"  # Trễ có phép
    LATE_UNEXCUSED = "LATE_UNEXCUSED"  # Trễ không phép
    ABSENT_EXCUSED = "ABSENT_EXCUSED"  # Vắng có phép
    ABSENT_UNEXCUSED = "ABSENT_UNEXCUSED"  # Vắng không phép
    COMPLETED = "COMPLETED"  # Đã hoàn thành / Đã checkout


class EvaluationType(str, Enum):
    """Loại đánh giá cá nhân 2 chiều"""

    TRAINER_TO_TRAINEE = "TRAINER_TO_TRAINEE"
    TRAINEE_TO_TRAINER = "TRAINEE_TO_TRAINER"


class EvaluationCriteriaCode(str, Enum):
    """Mã tiêu chí đánh giá chuẩn hóa hệ thống"""

    # Trainer evaluates Trainee
    ATTENDANCE_CONDUCT = "ATTENDANCE_CONDUCT"
    INTERACTION_CONTRIBUTION = "INTERACTION_CONTRIBUTION"
    ABSORPTION_COMPREHENSION = "ABSORPTION_COMPREHENSION"
    PRE_CLASS_PREPARATION = "PRE_CLASS_PREPARATION"

    # Trainee evaluates Trainer
    CONTENT_QUALITY = "CONTENT_QUALITY"
    TEACHING_METHOD = "TEACHING_METHOD"
    CLASS_ATMOSPHERE = "CLASS_ATMOSPHERE"
    PRACTICAL_VALUE = "PRACTICAL_VALUE"


class EvaluationCriterion(BaseModel):
    """Value Object đại diện cho một Tiêu chí đánh giá chuẩn hóa (Domain Value Object)."""

    code: str
    name: str
    description: str
    evaluation_type: EvaluationType

    @classmethod
    def from_code(
        cls,
        code: str | EvaluationCriteriaCode,
        default_type: EvaluationType | None = None,
    ) -> "EvaluationCriterion":
        raw_code = code.value if isinstance(code, Enum) else str(code)

        # Single Source of Truth cho toàn bộ hệ thống
        registry = {
            # Trainer evaluates Trainee
            EvaluationCriteriaCode.ATTENDANCE_CONDUCT.value: (
                "Chuyên cần & Tác phong",
                "Đúng giờ, tuân thủ nội quy và kỷ luật lớp học",
                EvaluationType.TRAINER_TO_TRAINEE,
            ),
            EvaluationCriteriaCode.INTERACTION_CONTRIBUTION.value: (
                "Mức độ Tương tác & Đóng góp",
                "Tích cực phát biểu, đặt câu hỏi, thảo luận sôi nổi",
                EvaluationType.TRAINER_TO_TRAINEE,
            ),
            EvaluationCriteriaCode.ABSORPTION_COMPREHENSION.value: (
                "Mức độ Tiếp thu & Hiểu bài",
                "Nắm bắt tốt kiến thức cốt lõi truyền đạt trong buổi học",
                EvaluationType.TRAINER_TO_TRAINEE,
            ),
            EvaluationCriteriaCode.PRE_CLASS_PREPARATION.value: (
                "Mức độ Chuẩn bị bài trước buổi học",
                "Đọc trước tài liệu, chuẩn bị bài tập / môi trường trước khi lên lớp",
                EvaluationType.TRAINER_TO_TRAINEE,
            ),
            # Trainee evaluates Trainer
            EvaluationCriteriaCode.CONTENT_QUALITY.value: (
                "Chất lượng Nội dung bài học",
                "Rõ ràng, thực tế, bố cục bài giảng hợp lý và dễ theo dõi",
                EvaluationType.TRAINEE_TO_TRAINER,
            ),
            EvaluationCriteriaCode.TEACHING_METHOD.value: (
                "Phương pháp Giảng dạy & Hỗ trợ",
                "Trainer truyền đạt dễ hiểu, nhiệt tình giải đáp các thắc mắc",
                EvaluationType.TRAINEE_TO_TRAINER,
            ),
            EvaluationCriteriaCode.CLASS_ATMOSPHERE.value: (
                "Không khí Lớp học & Sự tương tác",
                "Lôi cuốn, truyền cảm hứng và tạo động lực học tập tốt",
                EvaluationType.TRAINEE_TO_TRAINER,
            ),
            EvaluationCriteriaCode.PRACTICAL_VALUE.value: (
                "Giá trị Thu nhận & Tính ứng dụng",
                "Kiến thức thu nhận bổ ích, có thể ứng dụng trực tiếp vào thực tế",
                EvaluationType.TRAINEE_TO_TRAINER,
            ),
        }

        # Hỗ trợ cả mã có prefix cũ và alias trong mock/test data cũ
        legacy_aliases = {
            "TRAINER_TO_TRAINEE_ATTENDANCE": EvaluationCriteriaCode.ATTENDANCE_CONDUCT.value,
            "TRAINER_TO_TRAINEE_INTERACTION": EvaluationCriteriaCode.INTERACTION_CONTRIBUTION.value,
            "TRAINER_TO_TRAINEE_COMPREHENSION": EvaluationCriteriaCode.ABSORPTION_COMPREHENSION.value,
            "TRAINER_TO_TRAINEE_PREPARATION": EvaluationCriteriaCode.PRE_CLASS_PREPARATION.value,
            "TRAINEE_TO_TRAINER_CONTENT": EvaluationCriteriaCode.CONTENT_QUALITY.value,
            "TRAINEE_TO_TRAINER_METHOD": EvaluationCriteriaCode.TEACHING_METHOD.value,
            "TRAINEE_TO_TRAINER_ATMOSPHERE": EvaluationCriteriaCode.CLASS_ATMOSPHERE.value,
            "TRAINEE_TO_TRAINER_VALUE": EvaluationCriteriaCode.PRACTICAL_VALUE.value,
        }

        lookup_key = legacy_aliases.get(raw_code, raw_code)
        normalized = (
            lookup_key.replace("TRAINER_TO_TRAINEE_", "")
            .replace("TRAINEE_TO_TRAINER_", "")
        )

        if normalized in registry:
            name, desc, etype = registry[normalized]
            return cls(
                code=raw_code,
                name=name,
                description=desc,
                evaluation_type=etype,
            )

        # Fallback cho tiêu chí mở rộng/tùy biến
        fallback_type = default_type or (
            EvaluationType.TRAINER_TO_TRAINEE
            if "TRAINER" in raw_code
            else EvaluationType.TRAINEE_TO_TRAINER
        )
        return cls(
            code=raw_code,
            name=raw_code,
            description="",
            evaluation_type=fallback_type,
        )

    @classmethod
    def list_by_type(cls, eval_type: EvaluationType) -> list["EvaluationCriterion"]:
        """Lấy danh sách các tiêu chí chuẩn hóa theo loại đánh giá."""
        codes = (
            [
                EvaluationCriteriaCode.ATTENDANCE_CONDUCT,
                EvaluationCriteriaCode.INTERACTION_CONTRIBUTION,
                EvaluationCriteriaCode.ABSORPTION_COMPREHENSION,
                EvaluationCriteriaCode.PRE_CLASS_PREPARATION,
            ]
            if eval_type == EvaluationType.TRAINER_TO_TRAINEE
            else [
                EvaluationCriteriaCode.CONTENT_QUALITY,
                EvaluationCriteriaCode.TEACHING_METHOD,
                EvaluationCriteriaCode.CLASS_ATMOSPHERE,
                EvaluationCriteriaCode.PRACTICAL_VALUE,
            ]
        )
        return [cls.from_code(c, default_type=eval_type) for c in codes]


class CriteriaBreakdownSummary(BaseModel):
    """Value Object tổng hợp điểm trung bình của một tiêu chí (Domain Value Object)."""

    criterion: EvaluationCriterion
    average_score: float
    count: int

    @property
    def criteria_code(self) -> str:
        return self.criterion.code

    @property
    def criteria_name(self) -> str:
        return self.criterion.name

    @property
    def criteria_description(self) -> str:
        return self.criterion.description

    @property
    def evaluation_type(self) -> EvaluationType:
        return self.criterion.evaluation_type


class EvaluationGroupSummary(BaseModel):
    """Value Object tổng hợp kết quả của 1 nhóm đánh giá (Trainer->Trainee hoặc Trainee->Trainer)."""

    evaluation_type: EvaluationType
    total_evaluations: int
    average_score: float | None
    criteria_breakdown: list[CriteriaBreakdownSummary]

    @classmethod
    def from_evaluations(
        cls,
        eval_type: EvaluationType,
        evaluations: list[Any],
    ) -> "EvaluationGroupSummary":
        """Factory method đóng gói toàn bộ quy tắc tính toán điểm cho nhóm đánh giá."""
        from collections import defaultdict

        def _get_type_str(e: Any) -> str:
            t = getattr(e, "evaluation_type", "")
            return t.value if hasattr(t, "value") else str(t)

        relevant_evals = [
            e for e in evaluations if _get_type_str(e) == eval_type.value
        ]

        if not relevant_evals:
            return cls(
                evaluation_type=eval_type,
                total_evaluations=0,
                average_score=None,
                criteria_breakdown=[],
            )

        total_count = len(relevant_evals)
        avg_score = round(
            sum(e.average_score for e in relevant_evals) / total_count, 2
        )

        scores_by_code: dict[str, list[int]] = defaultdict(list)
        for e in relevant_evals:
            for s in getattr(e, "scores", []) or []:
                scores_by_code[s.criteria_code].append(s.score)

        breakdown = []
        for code, scores in scores_by_code.items():
            criterion = EvaluationCriterion.from_code(code, default_type=eval_type)
            breakdown.append(
                CriteriaBreakdownSummary(
                    criterion=criterion,
                    average_score=round(sum(scores) / len(scores), 2),
                    count=len(scores),
                )
            )

        return cls(
            evaluation_type=eval_type,
            total_evaluations=total_count,
            average_score=avg_score,
            criteria_breakdown=breakdown,
        )



class CapacityStatus(str, Enum):
    SAFE = "SAFE"  # < 2 người
    WARNING = "WARNING"  # = 2 người
    OVERLOAD = "OVERLOAD"  # >= 3 người


class CapacityMonitor(BaseModel):
    """Trạng thái cảnh báo quá tải (Value Object)"""

    MAX_CAPACITY: ClassVar[int] = 3
    WARNING_THRESHOLD: ClassVar[int] = 2
    OVERLOAD_THRESHOLD: ClassVar[int] = 3
    FORECAST_WINDOW_MINUTES: ClassVar[int] = 30
    EPSILON: ClassVar[int] = 0

    current_count: int = 0
    incoming_count: int = 0
    outgoing_count: int = 0
    future_count: int = 0
    epsilon: int = 0  # Use literal or field default
    max_capacity: int = 3

    status: CapacityStatus = CapacityStatus.SAFE
    last_updated: datetime

    @classmethod
    def calculate(
        cls,
        n_current: int,
        n_incoming: int,
        n_outgoing: int,
        epsilon: int = 0,
    ) -> "CapacityMonitor":
        """Tính toán capacity từ các thành phần"""
        n_future = n_current + n_incoming - n_outgoing + epsilon

        if n_future >= cls.OVERLOAD_THRESHOLD:
            status = CapacityStatus.OVERLOAD
        elif n_future >= cls.WARNING_THRESHOLD:
            status = CapacityStatus.WARNING
        else:
            status = CapacityStatus.SAFE

        return cls(
            current_count=n_current,
            incoming_count=n_incoming,
            outgoing_count=n_outgoing,
            future_count=n_future,
            epsilon=epsilon,
            max_capacity=cls.MAX_CAPACITY,
            status=status,
            last_updated=datetime.now(UTC),
        )
