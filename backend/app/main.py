from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_v1_router
from app.auth.providers import AuthModuleProvider
from app.billing.providers import BillingModuleProvider
from app.bonus_point.providers import BonusPointModuleProvider
from app.core.config import settings
from app.core.events import bootstrap_events
from app.core.logging_config import setup_logging
from app.core.scheduler import shutdown_scheduler, start_scheduler
from app.homework.providers import HomeworkModuleProvider
from app.meeting.providers import MeetingModuleProvider
from app.middleware.auth import set_user_context
from app.middleware.logging import logging_middleware
from app.permission_request.providers import PermissionRequestModuleProvider
from app.report.providers import ReportModuleProvider
from app.shared.application.response import BadRequestException
from app.shared.infrastructure.request_context import (
    _request_container_context,
    set_request_container,
)
from app.shared.providers import InfrastructureProvider
from app.team.providers import TeamModuleProvider
from app.user.providers import UserModuleProvider
from app.violation.providers import ViolationModuleProvider
from app.zalo.providers import ZaloModuleProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting application services...")

    # Event registration using Dishka
    await bootstrap_events(app.state.dishka_container)

    start_scheduler(app.state.dishka_container)
    logger.info("🚀 Application started")
    yield
    # Shutdown
    await app.state.dishka_container.close()
    shutdown_scheduler()
    logger.info("👋 Application shutdown")


def create_app():
    setup_logging()

    _app = FastAPI(
        title="DUT AI Manager API",
        description="API for DUT AI Manager",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
    )

    if settings.ENVIRONMENT != "local":
        _app.middleware("http")(logging_middleware)  # Inner

    _app.middleware("http")(set_user_context)  # Outer: sets user context for inner

    @_app.middleware("http")
    async def request_container_middleware(request, call_next):
        """Set the request-scoped dishka container in the context var."""
        token = None
        if hasattr(request.state, "dishka_container"):
            token = set_request_container(request.state.dishka_container)

        try:
            return await call_next(request)
        finally:
            if token:

                _request_container_context.reset(token)

    # Dishka Setup (Should be called AFTER middlewares to be the OUTERMOST)
    container = make_async_container(
        InfrastructureProvider(),
        AuthModuleProvider(),
        UserModuleProvider(),
        ViolationModuleProvider(),
        PermissionRequestModuleProvider(),
        ReportModuleProvider(),
        MeetingModuleProvider(),
        BonusPointModuleProvider(),
        HomeworkModuleProvider(),
        TeamModuleProvider(),
        BillingModuleProvider(),
        ZaloModuleProvider(),
    )
    setup_dishka(container, _app)

    # CORS middleware
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "https://test.phuocnguyn.id.vn",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API v1 router
    _app.include_router(api_v1_router)

    @_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        logger.error(f"Validation error for {request.method} {request.url.path}")
        logger.error(f"Error details: {exc.errors()}")

        # Try to get body from exception or request
        body = exc.body
        if body is None:
            try:
                body_bytes = await request.body()
                body = body_bytes.decode() if body_bytes else None
            except Exception:
                body = "<Could not read body>"

        logger.error(f"Request body: {body}")

        return JSONResponse(
            status_code=422,
            content={
                "is_success": False,
                "status_code": 422,
                "message": "Dữ liệu không hợp lệ",
                "data": exc.errors(),
            },
        )

    @_app.exception_handler(BadRequestException)
    async def bad_request_exception_handler(request, exc: BadRequestException):
        # Try to get body
        try:
            body_bytes = await request.body()
            body = body_bytes.decode() if body_bytes else "None"
        except Exception:
            body = "<Could not read body>"

        logger.error(
            f"Exception for {request.method} {request.url.path} with body {body}"
        )
        logger.error(f"Error details: {exc.message}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "is_success": False,
                "status_code": exc.status_code,
                "message": exc.message,
                "data": exc.data,
            },
        )

    @_app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        logger.error(
            f"HTTP {exc.status_code} error for {request.method} {request.url.path}"
        )
        logger.error(f"Error details: {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "is_success": False,
                "status_code": exc.status_code,
                "message": str(exc.detail),
                "data": None,
            },
        )

    @_app.exception_handler(Exception)
    async def exception_handler(request, exc):
        logger.error(f"Unhandled exception for {request.method} {request.url.path}")
        logger.exception(f"Error details: {exc}")

        return JSONResponse(
            status_code=500,
            content={
                "is_success": False,
                "status_code": 500,
                "message": "Đã xảy ra lỗi, liên hệ với admin",
                "data": None,
            },
        )

    @_app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return _app


app = create_app()
