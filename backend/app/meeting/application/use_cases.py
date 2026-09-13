"""
Meeting Application Use Cases — Facade and re-exports.

Provides clean architecture modularization while maintaining 100% backwards-compatible
imports for Dishka providers, controllers, and scheduled jobs.
"""

from datetime import date

from app.meeting.application.attendance_use_cases import (
    CheckMeetingAttendanceUseCase,
    UpdateParticipantStatusUseCase,
)
from app.meeting.application.capacity_use_cases import CalculateCurrentCapacityUseCase
from app.meeting.application.checkin_use_cases import (
    CheckInUseCase,
    CheckInWithCardUseCase,
    CheckOutUseCase,
)
from app.meeting.application.crud_use_cases import (
    CreateMeetingUseCase,
    DeleteMeetingUseCase,
    GetMeetingsUseCase,
    MeetingUseCases,
    UpdateMeetingUseCase,
)
from app.meeting.domain.entity import Meeting
from app.meeting.infrastructure.repository import MeetingRepository


__all__ = [
    "GetMeetingsUseCase",
    "CreateMeetingUseCase",
    "UpdateMeetingUseCase",
    "DeleteMeetingUseCase",
    "CheckInUseCase",
    "CheckInWithCardUseCase",
    "CheckOutUseCase",
    "CheckMeetingAttendanceUseCase",
    "UpdateParticipantStatusUseCase",
    "CalculateCurrentCapacityUseCase",
    "MeetingUseCases",
]
