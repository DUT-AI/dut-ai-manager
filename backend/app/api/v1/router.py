from app.api.v1.controllers import (
    auth_controller,
    bonus_point_controller,
    permission_request_controller,
    role_api_key_controller,
    report_controller,
    role_permission_controller,
    user_controller,
    violation_controller,
    team_controller,
    homework_controller,
    homework_submission_controller,
    meeting_controller,
    zalo_controller,
    zalo_bot_controller,
)
from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1")

# List of routers to include
routers = [
    auth_controller.router,
    bonus_point_controller.router,
    permission_request_controller.router,
    role_api_key_controller.router,
    report_controller.router,
    role_permission_controller.router,
    user_controller.router,
    violation_controller.router,
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
