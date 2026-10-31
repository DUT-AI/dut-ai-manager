"""Meeting repositories re-export shim for backward compatibility.

All repositories have been decomposed into dedicated files in:
`app.meeting.infrastructure.repositories`
"""

from .repositories import (
    MeetingEvaluationRepository,
    MeetingOverallEvaluationRepository,
    MeetingRepository,
    ParticipantRepository,
)

__all__ = [
    "MeetingEvaluationRepository",
    "MeetingOverallEvaluationRepository",
    "MeetingRepository",
    "ParticipantRepository",
]
