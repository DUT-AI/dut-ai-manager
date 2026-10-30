from datetime import datetime, timezone

from app.meeting.domain.entity import EvaluationScoreItem, MeetingOverallEvaluation
from app.meeting.infrastructure.repository import (
    MeetingOverallEvaluationRepository,
    MeetingRepository,
)
from app.shared.application.response import BadRequestException


class SubmitMeetingOverallEvaluationUseCase:
    """Trainer gửi đánh giá tổng thể cho toàn bộ buổi học (Quan hệ 1 - 1 với Meeting)."""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        overall_eval_repo: MeetingOverallEvaluationRepository,
    ):
        self.meeting_repo = meeting_repo
        self.overall_eval_repo = overall_eval_repo

    async def execute(
        self,
        meeting_id: int,
        trainer_id: int,
        scores_data: list[dict],
        general_feedback: str | None = None,
    ) -> MeetingOverallEvaluation:
        # 1. Kiểm tra Buổi học
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi học", status_code=404)

        now = datetime.now(timezone.utc)
        is_open, message = meeting.is_evaluation_open(now)
        if not is_open:
            raise BadRequestException(message)

        # 2. Chuyển đổi điểm số 4 tiêu chí chuẩn
        score_items = [
            EvaluationScoreItem(
                criteria_code=item["criteria_code"],
                score=item["score"],
            )
            for item in scores_data
        ]

        # 3. Kiểm tra xem đã có đánh giá tổng thể cho meeting chưa (hỗ trợ cập nhật nếu đã có)
        existing = self.overall_eval_repo.get_by_meeting_id(meeting_id)
        if existing:
            existing.scores = score_items
            existing.general_feedback = general_feedback
            existing.trainer_id = trainer_id
            existing.calculate_average()
            existing.updated_at = now
            return self.overall_eval_repo.save(existing)

        # 4. Tạo mới Entity MeetingOverallEvaluation
        overall_eval = MeetingOverallEvaluation(
            meeting_id=meeting_id,
            trainer_id=trainer_id,
            scores=score_items,
            general_feedback=general_feedback,
            created_at=now,
            updated_at=now,
        )
        overall_eval.calculate_average()

        return self.overall_eval_repo.save(overall_eval)
