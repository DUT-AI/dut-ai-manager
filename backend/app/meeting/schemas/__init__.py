"""Meeting schemas package.

Decomposed DTO schemas for the meeting domain:
- `meeting_schemas.py`: Meeting lifecycle, CRUD, response DTOs, seats
- `participant_schemas.py`: Attendance check-in, card check-in, checkout
- `evaluation_schemas.py`: Evaluations, criteria breakdowns
"""

from .evaluation_schemas import (
    CriteriaAverageScoreDto,
    EvaluationResponse,
    EvaluationScoreItemDto,
    EvaluationScoreItemSubmitDto,
    MeetingEvaluationSummaryResponse,
    MeetingOverallEvaluationResponse,
    SubmitMeetingOverallEvaluationRequest,
    TraineeSubmitEvaluationRequest,
    TrainerSubmitEvaluationRequest,
)
from .meeting_schemas import (
    MeetingCreate,
    MeetingDetailResponse,
    MeetingResponse,
    MeetingSeatAvailabilityDto,
    MeetingUpdate,
    UserRefDto,
)
from .participant_schemas import (
    CheckInWithCardRequest,
    CheckOutRequest,
    ParticipantResponse,
    UpdateParticipantStatusRequest,
)

__all__ = [
    "CheckInWithCardRequest",
    "CheckOutRequest",
    "CriteriaAverageScoreDto",
    "EvaluationResponse",
    "EvaluationScoreItemDto",
    "EvaluationScoreItemSubmitDto",
    "MeetingCreate",
    "MeetingDetailResponse",
    "MeetingEvaluationSummaryResponse",
    "MeetingOverallEvaluationResponse",
    "MeetingResponse",
    "MeetingSeatAvailabilityDto",
    "MeetingUpdate",
    "ParticipantResponse",
    "SubmitMeetingOverallEvaluationRequest",
    "TraineeSubmitEvaluationRequest",
    "TrainerSubmitEvaluationRequest",
    "UpdateParticipantStatusRequest",
    "UserRefDto",
]
