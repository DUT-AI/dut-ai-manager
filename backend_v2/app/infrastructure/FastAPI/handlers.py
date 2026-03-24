from app.shared.api_response import BadRequestException
from app.shared.base_exception import DomainException
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.error(f"Validation error for {request.method} {request.url.path}")
        logger.error(f"Error details: {exc.errors()}")

        # Try to get body from request
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

    @app.exception_handler(BadRequestException)
    async def bad_request_exception_handler(request: Request, exc: BadRequestException):
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

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        logger.warning(f"Domain rule violation for {request.method} {request.url.path}")
        logger.warning(f"Message: {exc.message}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "is_success": False,
                "status_code": exc.status_code,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
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

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
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
