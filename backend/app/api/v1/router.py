from fastapi import APIRouter

from app.api.v1.controllers import example_controller

api_v1_router = APIRouter()

# Include all controllers here
api_v1_router.include_router(
    example_controller.router,
    prefix="/examples",
    tags=["examples"],
)
