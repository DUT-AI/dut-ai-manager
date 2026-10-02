
from app.meeting.domain.entity import EvaluationScoreItem, MeetingEvaluation
from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.utils.datetime import get_current_utc7_time


class SubmitTraineeEvaluationUseCase:
    """Trainee gửi đánh giá dành cho Trainer của buổi học (có tùy chọn ẩn danh)."""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.meeting_repo = meeting_repo
        self.evaluation_repo = evaluation_repo
        self.event_bus = event_bus

    async def execute(
        self,
        meeting_id: int,
        reviewer_id: int,
        target_user_id: int | None,
        scores_data: list[dict],
        is_anonymous: bool = False,
        feedback_text: str | None = None,
    ) -> MeetingEvaluation:
        # 1. Kiểm tra Buổi học
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi học", status_code=404)

        now = get_current_utc7_time()
        is_open, msg = meeting.is_evaluation_open(now)
        if not is_open:
            raise BadRequestException(msg)

        resolved_target_id = target_user_id or meeting.created_by
        if not resolved_target_id:
            raise BadRequestException(
                "Không xác định được giảng viên (Trainer) của buổi học"
            )

        # 2. Kiểm tra Trainee (người đánh giá) có tham gia không
        participant = next(
            (p for p in meeting.participants if p.user_id == reviewer_id),
            None,
        )
        if not participant:
            raise BadRequestException("Bạn không thuộc danh sách tham gia buổi học này")

        if participant.status not in (
            ParticipantStatus.JOINED,
            ParticipantStatus.LATE_EXCUSED,
            ParticipantStatus.LATE_UNEXCUSED,
            ParticipantStatus.COMPLETED,
        ):
            raise BadRequestException(
                "Bạn chỉ có thể đánh giá khi đã tham gia buổi học thực tế"
            )

        # 3. Chống đánh giá trùng lặp
        existing = self.evaluation_repo.get_by_meeting_and_users(
            meeting_id=meeting_id,
            reviewer_id=reviewer_id,
            target_user_id=resolved_target_id,
        )
        if existing:
            raise BadRequestException(
                "Bạn đã gửi đánh giá cho Trainer trong buổi học này rồi"
            )

        # 4. Tạo entity và tính điểm
        score_items = [
            EvaluationScoreItem(
                criteria_code=item["criteria_code"],
                score=item["score"],
            )
            for item in scores_data
        ]

        eval_entity = MeetingEvaluation(
            meeting_id=meeting_id,
            reviewer_id=reviewer_id,
            target_user_id=resolved_target_id,
            evaluation_type=EvaluationType.TRAINEE_TO_TRAINER,
            is_anonymous=is_anonymous,
            scores=score_items,
            feedback_text=feedback_text,
            created_at=now,
            updated_at=now,
        )
        eval_entity.calculate_average()

        saved = self.evaluation_repo.save(eval_entity)
        return saved
