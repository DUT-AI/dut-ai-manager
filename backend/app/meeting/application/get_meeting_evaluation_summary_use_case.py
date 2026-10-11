from app.meeting.domain.value_objects import (
    EvaluationType,
    EvaluationGroupSummary,
)
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingOverallEvaluationRepository,
    MeetingRepository,
)
from app.meeting.schemas import (
    CriteriaAverageScoreDto,
    EvaluationResponse,
    MeetingEvaluationSummaryResponse,
    MeetingOverallEvaluationResponse,
)
from app.shared.application.response import BadRequestException


class GetMeetingEvaluationSummaryUseCase:
    """Lấy báo cáo tổng hợp kết quả đánh giá của Buổi học/Meeting."""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
        overall_eval_repo: MeetingOverallEvaluationRepository | None = None,
    ):
        self.meeting_repo = meeting_repo
        self.evaluation_repo = evaluation_repo
        self.overall_eval_repo = overall_eval_repo

    async def execute(
        self, meeting_id: int, current_user_id: int | None = None
    ) -> MeetingEvaluationSummaryResponse:
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

        # Chuẩn hóa danh sách đánh giá trả về (chính chủ thấy được reviewer_id của mình)
        evaluation_responses = [
            EvaluationResponse.from_domain(e, current_user_id=current_user_id)
            for e in all_evaluations
        ]

        # Tìm đánh giá mà chính user này đã gửi cho Trainer (nếu có)
        my_eval_entity = (
            next(
                (
                    e
                    for e in all_evaluations
                    if e.evaluation_type == EvaluationType.TRAINEE_TO_TRAINER
                    and e.reviewer_id == current_user_id
                ),
                None,
            )
            if current_user_id
            else None
        )
        my_eval_dto = (
            EvaluationResponse.from_domain(
                my_eval_entity, current_user_id=current_user_id
            )
            if my_eval_entity
            else None
        )

        overall_eval_dto = None
        if self.overall_eval_repo:
            overall_entity = self.overall_eval_repo.get_by_meeting_id(meeting_id)
            if overall_entity:
                overall_eval_dto = MeetingOverallEvaluationResponse.from_domain(overall_entity)

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
            my_evaluation=my_eval_dto,
            overall_evaluation=overall_eval_dto,
        )

