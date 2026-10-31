"""Domain entities re-export shim for backward compatibility.

All entities have been partitioned into dedicated domain files:
- `meeting.py`: Meeting aggregate root
- `participant.py`: MeetingParticipant entity & attendance methods
- `evaluation.py`: MeetingEvaluation, MeetingOverallEvaluation, EvaluationScoreItem
- `value_objects.py`: UserRef, ParticipantStatus, EvaluationType, etc.
"""

from app.meeting.domain.evaluation import (
    EvaluationScoreItem,
    MeetingEvaluation,
    MeetingOverallEvaluation,
)
from app.meeting.domain.meeting import Meeting
from app.meeting.domain.participant import MeetingParticipant
from app.meeting.domain.value_objects import (
    EvaluationType,
    ParticipantStatus,
    UserRef,
)

__all__ = [
    "EvaluationScoreItem",
    "EvaluationType",
    "Meeting",
    "MeetingEvaluation",
    "MeetingOverallEvaluation",
    "MeetingParticipant",
    "ParticipantStatus",
    "UserRef",
]
