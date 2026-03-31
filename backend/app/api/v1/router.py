from app.api.v1.controllers import (
    bonus_point_controller,
    permission_request_controller,
    role_api_key_controller,
    report_controller,
    role_permission_controller,
    team_controller,
    homework_controller,
    homework_submission_controller,
    meeting_controller,
    zalo_controller,
    zalo_bot_controller,
)

from app.violation.controller import router as violation_router
from app.user.controller import router as user_router
from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1")

# List of routers to include
routers = [
    # auth_router, # we'll update this when auth is refactored
    bonus_point_controller.router,
    permission_request_controller.router,
    role_api_key_controller.router,
    report_controller.router,
    role_permission_controller.router,
    user_router,
    violation_router,
    team_controller.router,
    homework_controller.router,
    homework_submission_controller.router,
    meeting_controller.router,
    zalo_controller.router,
    zalo_bot_controller.router,
]

# Include all routers in a single loop
for router in routers:
    api_v1_router.include_router(router)
