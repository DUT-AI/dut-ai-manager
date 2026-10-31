"""Meeting domain package.

Re-exports core domain entities, events, and value objects.
"""

from app.meeting.domain.evaluation import (
    EvaluationCriteria,
    EvaluationCriteriaCode,
    EvaluationCriterion,
    EvaluationScoreItem,
    MeetingEvaluation,
    MeetingOverallEvaluation,
)
from app.meeting.domain.events import (
    MeetingAbsenceDetected,
    MeetingCreated,
    MeetingUpdated,
    ParticipantAbsenceRecorded,
    ParticipantCheckedIn,
    ParticipantCheckedOut,
    ParticipantLateRecorded,
)
from app.meeting.domain.meeting import Meeting
from app.meeting.domain.participant import MeetingParticipant
from app.meeting.domain.value_objects import (
    CapacityMonitor,
    CapacityStatus,
    CriteriaBreakdownSummary,
    EvaluationGroupSummary,
    EvaluationType,
    ParticipantStatus,
    UserRef,
)

__all__ = [
    "CapacityMonitor",
    "CapacityStatus",
    "CriteriaBreakdownSummary",
    "EvaluationCriteria",
    "EvaluationCriteriaCode",
    "EvaluationCriterion",
    "EvaluationGroupSummary",
    "EvaluationScoreItem",
    "EvaluationType",
    "Meeting",
    "MeetingAbsenceDetected",
    "MeetingCreated",
    "MeetingEvaluation",
    "MeetingOverallEvaluation",
    "MeetingParticipant",
    "MeetingUpdated",
    "ParticipantAbsenceRecorded",
    "ParticipantCheckedIn",
    "ParticipantCheckedOut",
    "ParticipantLateRecorded",
    "ParticipantStatus",
    "UserRef",
]
