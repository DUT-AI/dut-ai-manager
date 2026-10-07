from app.meeting.domain.value_objects import (
    EvaluationType,
    EvaluationGroupSummary,
)
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
)
from app.meeting.schemas import (
    CriteriaAverageScoreDto,
    EvaluationResponse,
    MeetingEvaluationSummaryResponse,
)
from app.shared.application.response import BadRequestException


class GetMeetingEvaluationSummaryUseCase:
    """Lấy báo cáo tổng hợp kết quả đánh giá của Buổi học/Meeting."""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
    ):
        self.meeting_repo = meeting_repo
        self.evaluation_repo = evaluation_repo

    async def execute(self, meeting_id: int) -> MeetingEvaluationSummaryResponse:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi học", status_code=404)

        all_evaluations = self.evaluation_repo.get_evaluations_by_meeting(meeting_id)

        # Tính toán phân nhóm thông qua Domain Value Object EvaluationGroupSummary
        trainer_summary = EvaluationGroupSummary.from_evaluations(
            EvaluationType.TRAINER_TO_TRAINEE, all_evaluations
        )
        trainee_summary = EvaluationGroupSummary.from_evaluations(
            EvaluationType.TRAINEE_TO_TRAINER, all_evaluations
        )

        total_count = len(all_evaluations)
        overall_avg = (
            round(sum(e.average_score for e in all_evaluations) / total_count, 2)
            if total_count > 0
            else 0.0
        )

        # Chuyển đổi CriteriaBreakdownSummary sang DTO
        all_criteria_breakdown = [
            CriteriaAverageScoreDto.from_summary(cb)
            for cb in (
                trainer_summary.criteria_breakdown + trainee_summary.criteria_breakdown
            )
        ]

        # Chuẩn hóa danh sách đánh giá trả về
        evaluation_responses = [
            EvaluationResponse.from_domain(e) for e in all_evaluations
        ]

        return MeetingEvaluationSummaryResponse(
            meeting_id=meeting_id,
            total_evaluations=total_count,
            overall_average_score=overall_avg,
            criteria_breakdown=all_criteria_breakdown,
            evaluations=evaluation_responses,
            total_trainer_evaluations=trainer_summary.total_evaluations,
            total_trainee_evaluations=trainee_summary.total_evaluations,
            trainer_average_score=trainer_summary.average_score,
            trainee_average_score=trainee_summary.average_score,
        )

