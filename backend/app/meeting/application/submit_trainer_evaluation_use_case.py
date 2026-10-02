from app.meeting.domain.entity import EvaluationScoreItem, MeetingEvaluation
from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
)
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.utils.datetime import get_current_utc7_time


class SubmitTrainerEvaluationUseCase:
    """Trainer thực hiện đánh giá một Trainee tham gia buổi học."""

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
        target_user_id: int,
        scores_data: list[dict],
        feedback_text: str | None = None,
    ) -> MeetingEvaluation:
        # 1. Kiểm tra Buổi học
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi học", status_code=404)

        now = get_current_utc7_time()
        is_open, message = meeting.is_evaluation_open(now)
        if not is_open:
            raise BadRequestException(message)

        # 2. Kiểm tra Trainee có trong danh sách và đã tham gia không
        participant = next(
            (p for p in meeting.participants if p.user_id == target_user_id),
            None,
        )
        if not participant:
            raise BadRequestException(
                "Học viên này không thuộc danh sách tham gia buổi học"
            )

        if participant.status in (
            ParticipantStatus.ABSENT_EXCUSED,
            ParticipantStatus.ABSENT_UNEXCUSED,
        ):
            raise BadRequestException(
                "Không thể đánh giá học viên đã vắng mặt trong buổi học"
            )

        # 3. Chống đánh giá trùng lặp
        existing = self.evaluation_repo.get_by_meeting_and_users(
            meeting_id=meeting_id,
            reviewer_id=reviewer_id,
            target_user_id=target_user_id,
        )
        if existing:
            raise BadRequestException(
                "Bạn đã gửi đánh giá cho học viên này trong buổi học"
            )

        # 4. Khởi tạo Entity và tính điểm trung bình
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
            target_user_id=target_user_id,
            evaluation_type=EvaluationType.TRAINER_TO_TRAINEE,
            is_anonymous=False,
            scores=score_items,
            feedback_text=feedback_text,
            created_at=now,
            updated_at=now,
        )
        eval_entity.calculate_average()

        saved = self.evaluation_repo.save(eval_entity)
        return saved
