"""ASGI Middleware to extract user ID from JWT and set it in request context.

This allows SQLAlchemy audit events to auto-populate created_by/updated_by
without passing user ID through every function call.
"""

import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.settings import JWTSetting
from app.shared.request_context import current_user_id_var


class AuditContextMiddleware(BaseHTTPMiddleware):
    """Extract user ID from JWT cookie/header and set ContextVar."""

    def __init__(self, app, settings: JWTSetting | None = None) -> None:  # type: ignore[override]
        super().__init__(app)
        self._settings = settings or JWTSetting()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        user_id = self._extract_user_id(request)
        token = current_user_id_var.set(user_id)
        try:
            return await call_next(request)
        finally:
            current_user_id_var.reset(token)

    def _extract_user_id(self, request: Request) -> int | None:
        """Best-effort extraction — never raises, returns None on failure."""
        raw_token = request.cookies.get("access_token")
        if not raw_token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                raw_token = auth_header.split(" ", 1)[1]

        if not raw_token:
            return None

        try:
            payload = jwt.decode(
                raw_token,
                self._settings.SECRET_KEY,
                algorithms=["HS256"],
            )
            return int(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError, TypeError):
            return None
