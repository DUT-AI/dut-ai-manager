from app.auth.presentation.router import router as auth_router
from app.infrastructure.FastAPI import setup_provider
from app.infrastructure.FastAPI.handlers import setup_exception_handlers
from app.infrastructure.FastAPI.router import setup_router
from app.user.presentation.router import router as user_router
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Initialize DI container
    container = setup_provider()

    # Create app
    app = FastAPI(
        title="Dut AI Manager V2",  # TODO: Use app_settings.APP_NAME
        version="1.0.0",  # TODO: Use app_settings.API_VERSION
        debug=True,  # TODO: Use app_settings.DEBUG
    )

    setup_exception_handlers(app)

    # Wire container
    setup_dishka(container, app)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Use app_settings.CORS_ORIGINS
        allow_credentials=True,  # TODO: Use app_settings.CORS_CREDENTIALS
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    setup_router(app)

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app
