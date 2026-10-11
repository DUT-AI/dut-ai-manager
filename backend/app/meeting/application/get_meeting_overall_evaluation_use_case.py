from app.meeting.domain.entity import MeetingOverallEvaluation
from app.meeting.infrastructure.repository import (
    MeetingOverallEvaluationRepository,
    MeetingRepository,
)
from app.shared.application.response import BadRequestException


class GetMeetingOverallEvaluationUseCase:
    """Lấy kết quả đánh giá tổng thể buổi học do Trainer gửi (Công khai cho toàn bộ học viên tham gia)."""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        overall_eval_repo: MeetingOverallEvaluationRepository,
    ):
        self.meeting_repo = meeting_repo
        self.overall_eval_repo = overall_eval_repo

    async def execute(self, meeting_id: int) -> MeetingOverallEvaluation | None:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi học", status_code=404)

        return self.overall_eval_repo.get_by_meeting_id(meeting_id)
