from collections import defaultdict

from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
)
from app.meeting.schemas import (
    CRITERIA_DESC_MAP,
    CRITERIA_NAME_MAP,
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

        if not all_evaluations:
            return MeetingEvaluationSummaryResponse(
                meeting_id=meeting_id,
                total_evaluations=0,
                overall_average_score=0.0,
                criteria_breakdown=[],
                evaluations=[],
            )

        total_count = len(all_evaluations)
        overall_avg = round(
            sum(e.average_score for e in all_evaluations) / total_count, 2
        )

        # Tính trung bình theo từng tiêu chí
        criteria_scores = defaultdict(list)
        for e in all_evaluations:
            for s in e.scores:
                criteria_scores[s.criteria_code].append(s.score)

        criteria_breakdown = [
            CriteriaAverageScoreDto(
                criteria_code=code,
                criteria_name=CRITERIA_NAME_MAP.get(code, code),
                criteria_description=CRITERIA_DESC_MAP.get(code, ""),
                average_score=round(sum(scores) / len(scores), 2),
                count=len(scores),
            )
            for code, scores in criteria_scores.items()
        ]

        # Chuẩn hóa danh sách đánh giá trả về (dùng EvaluationResponse.from_domain chuẩn hóa)
        evaluation_responses = [
            EvaluationResponse.from_domain(e) for e in all_evaluations
        ]

        return MeetingEvaluationSummaryResponse(
            meeting_id=meeting_id,
            total_evaluations=total_count,
            overall_average_score=overall_avg,
            criteria_breakdown=criteria_breakdown,
            evaluations=evaluation_responses,
        )
