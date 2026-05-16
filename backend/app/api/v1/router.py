from fastapi import APIRouter

from app.auth.controller import router as auth_router
from app.billing.controller import router as billing_router
from app.bonus_point.controller import router as bonus_point_router
from app.homework.controller import (
    router as homework_router,
)
from app.homework.controller import (
    submission_router as homework_submission_router,
)
from app.meeting.controller import router as meeting_router
from app.permission_request.controller import router as permission_request_router
from app.rbac.controller import router as rbac_router
from app.report.controller import router as report_router
from app.team.controller import router as team_router
from app.user.controller import router as user_router
from app.violation.controller import router as violation_router
from app.zalo.controller import router as zalo_router

api_v1_router = APIRouter(prefix="/api/v1")

# List of routers to include
routers = [
    auth_router,
    bonus_point_router,
    permission_request_router,
    report_router,
    rbac_router,
    user_router,
    violation_router,
    team_router,
    homework_router,
    homework_submission_router,
    meeting_router,
    zalo_router,
    billing_router,
]

# Include all routers in a single loop
for router in routers:
    api_v1_router.include_router(router)
