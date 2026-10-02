from app.meeting.domain.entity import MeetingEvaluation
from app.meeting.domain.value_objects import EvaluationType
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
)
from app.shared.application.response import BadRequestException


class GetMyEvaluationResultUseCase:
    """Trainee xem kết quả đánh giá và nhận xét mà Trainer dành cho mình.

    Yêu cầu: Trainee phải hoàn thành đánh giá Trainer trước thì mới mở khóa xem kết quả.
    """

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
    ):
        self.meeting_repo = meeting_repo
        self.evaluation_repo = evaluation_repo

    async def execute(
        self, meeting_id: int, current_user_id: int
    ) -> MeetingEvaluation | None:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException("Không tìm thấy buổi học", status_code=404)

        if not meeting.enable_evaluation:
            return None

        # 1. Kiểm tra Trainee đã đánh giá Trainer chưa
        trainee_eval = self.evaluation_repo.get_by_meeting_and_users(
            meeting_id=meeting_id,
            reviewer_id=current_user_id,
            target_user_id=meeting.created_by or 0,
        )
        if not trainee_eval:
            # Tìm xem có bất kỳ đánh giá nào do Trainee gửi trong meeting không
            trainee_evals = self.evaluation_repo.get_evaluations_by_meeting(
                meeting_id=meeting_id,
                evaluation_type=EvaluationType.TRAINEE_TO_TRAINER.value,
            )
            has_evaluated = any(e.reviewer_id == current_user_id for e in trainee_evals)
            if not has_evaluated:
                raise BadRequestException(
                    "Bạn cần hoàn thành đánh giá Trainer trước khi xem kết quả đánh giá của mình",
                    status_code=403,
                )

        # 2. Lấy phiếu đánh giá mà Trainer đã chấm cho Trainee
        evaluations_received = self.evaluation_repo.get_evaluations_for_user_in_meeting(
            meeting_id=meeting_id,
            target_user_id=current_user_id,
        )
        trainer_eval = next(
            (
                e
                for e in evaluations_received
                if e.evaluation_type == EvaluationType.TRAINER_TO_TRAINEE
            ),
            None,
        )
        return trainer_eval
