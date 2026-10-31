"""Composite root router for the Meeting domain.

Mounts modular sub-routers:
- `attendance_router`: check-in, check-in with card, check-out, status
- `evaluation_router`: trainer/trainee and meeting overall evaluations
- `meeting_router`: meeting CRUD, seat availability, capacity, SSE stream
"""

from fastapi import APIRouter

from app.meeting.controllers.attendance_controller import router as attendance_router
from app.meeting.controllers.dependencies import (
    check_meeting_evaluation_permission,
    check_meeting_ownership,
)
from app.meeting.controllers.evaluation_controller import router as evaluation_router
from app.meeting.controllers.meeting_controller import router as meeting_router

router = APIRouter()

# Mount sub-routers in priority order:
# Specific attendance and evaluation routes are included first so that static
# paths like /check-in, /available-seats take precedence over parameter routes.
router.include_router(attendance_router)
router.include_router(evaluation_router)
router.include_router(meeting_router)

__all__ = [
    "check_meeting_evaluation_permission",
    "check_meeting_ownership",
    "router",
]
