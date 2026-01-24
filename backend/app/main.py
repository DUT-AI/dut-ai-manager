from contextlib import asynccontextmanager

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.middleware.auth import set_user_context
from app.middleware.logging import logging_middleware
from app.schemas.response import BadRequestException
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    start_scheduler()
    logger.info("🚀 Application started")
    yield
    # Shutdown
    shutdown_scheduler()
    logger.info("👋 Application shutdown")


def create_app():
    setup_logging()

    _app = FastAPI(
        title="DUT AI Manager API",
        description="API for DUT AI Manager",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register middlewares
    # Note: Middlewares are executed in reverse order of registration for @app.middleware
    # or last-added-runs-first for add_middleware.
    # To have set_user_context run before logging_middleware:

    if settings.ENVIRONMENT != "local":
        _app.middleware("http")(logging_middleware)  # Inner

    _app.middleware("http")(set_user_context)  # Outer: sets user context for inner

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
