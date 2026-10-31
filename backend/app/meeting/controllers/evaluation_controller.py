from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser
from app.meeting.application import (
    GetMeetingEvaluationSummaryUseCase,
    GetMeetingOverallEvaluationUseCase,
    GetMyEvaluationResultUseCase,
    SubmitMeetingOverallEvaluationUseCase,
    SubmitTraineeEvaluationUseCase,
    SubmitTrainerEvaluationUseCase,
)
from app.meeting.controllers.dependencies import check_meeting_evaluation_permission
from app.meeting.schemas import (
    EvaluationResponse,
    MeetingEvaluationSummaryResponse,
    MeetingOverallEvaluationResponse,
    SubmitMeetingOverallEvaluationRequest,
    TraineeSubmitEvaluationRequest,
    TrainerSubmitEvaluationRequest,
)
from app.shared.application.response import ApiResponse

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post(
    "/{meeting_id}/evaluations/overall",
    response_model=ApiResponse[MeetingOverallEvaluationResponse],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def submit_meeting_overall_evaluation(
    meeting_id: int,
    data: SubmitMeetingOverallEvaluationRequest,
    uc: FromDishka[SubmitMeetingOverallEvaluationUseCase],
    current_user: CurrentUser,
    _: Annotated[None, Depends(check_meeting_evaluation_permission)],
):
    result = await uc.execute(
        meeting_id=meeting_id,
        trainer_id=current_user.user_id,
        scores_data=[s.model_dump() for s in data.scores],
        general_feedback=data.general_feedback,
    )
    return ApiResponse.success(
        data=MeetingOverallEvaluationResponse.from_domain(result),
        message="Đánh giá tổng thể buổi học thành công",
    )


@router.get(
    "/{meeting_id}/evaluations/overall",
    response_model=ApiResponse[MeetingOverallEvaluationResponse | None],
)
@inject
async def get_meeting_overall_evaluation(
    meeting_id: int,
    uc: FromDishka[GetMeetingOverallEvaluationUseCase],
    _current_user: CurrentUser,
):
    """Lấy đánh giá tổng thể của buổi học (Công khai cho toàn bộ thành viên)."""
    result = await uc.execute(meeting_id=meeting_id)
    data = MeetingOverallEvaluationResponse.from_domain(result) if result else None
    return ApiResponse.success(data=data)


@router.post(
    "/{meeting_id}/evaluations/trainer",
    response_model=ApiResponse[EvaluationResponse],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def submit_trainer_evaluation(
    meeting_id: int,
    data: TrainerSubmitEvaluationRequest,
    uc: FromDishka[SubmitTrainerEvaluationUseCase],
    current_user: CurrentUser,
    _: Annotated[None, Depends(check_meeting_evaluation_permission)],
):
    """Trainer gửi đánh giá cho 1 Trainee cụ thể trong buổi học."""

    result = await uc.execute(
        meeting_id=meeting_id,
        reviewer_id=current_user.user_id,
        target_user_id=data.target_user_id,
        scores_data=[s.model_dump() for s in data.scores],
        feedback_text=data.feedback_text,
    )
    return ApiResponse.success(
        data=EvaluationResponse.from_domain(result),
        message="Đánh giá học viên thành công",
    )


@router.post(
    "/{meeting_id}/evaluations/trainee",
    response_model=ApiResponse[EvaluationResponse],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def submit_trainee_evaluation(
    meeting_id: int,
    data: TraineeSubmitEvaluationRequest,
    uc: FromDishka[SubmitTraineeEvaluationUseCase],
    current_user: CurrentUser,
):
    """Trainee gửi đánh giá cho Trainer của buổi học (hỗ trợ ẩn danh)."""
    result = await uc.execute(
        meeting_id=meeting_id,
        reviewer_id=current_user.user_id,
        target_user_id=data.target_user_id,
        scores_data=[s.model_dump() for s in data.scores],
        is_anonymous=data.is_anonymous,
        feedback_text=data.feedback_text,
    )
    return ApiResponse.success(
        data=EvaluationResponse.from_domain(
            result, current_user_id=current_user.user_id
        ),
        message="Gửi đánh giá Trainer thành công",
    )


@router.get(
    "/{meeting_id}/evaluations/summary",
    response_model=ApiResponse[MeetingEvaluationSummaryResponse],
)
@inject
async def get_meeting_evaluation_summary(
    meeting_id: int,
    uc: FromDishka[GetMeetingEvaluationSummaryUseCase],
    current_user: CurrentUser,
):
    """Lấy báo cáo tổng hợp kết quả đánh giá của buổi học."""
    summary = await uc.execute(
        meeting_id=meeting_id, current_user_id=current_user.user_id
    )
    return ApiResponse.success(data=summary)


@router.get(
    "/{meeting_id}/evaluations/my-result",
    response_model=ApiResponse[EvaluationResponse | None],
)
@inject
async def get_my_evaluation_result(
    meeting_id: int,
    uc: FromDishka[GetMyEvaluationResultUseCase],
    current_user: CurrentUser,
):
    """Trainee xem đánh giá nhận được (cần đánh giá Trainer trước)."""
    result = await uc.execute(
        meeting_id=meeting_id, current_user_id=current_user.user_id
    )
    data = EvaluationResponse.from_domain(result) if result else None
    return ApiResponse.success(data=data)


__all__ = ["router"]
