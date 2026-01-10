from fastapi import Request
from app.core.context import set_current_user_id
from app.utils.password import decode_token


async def set_user_context(request: Request, call_next):
    """Middleware to set current_user_id in context from JWT token."""
    token = request.cookies.get("access_token")
    auth_header = request.headers.get("Authorization")

    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if token:
        payload = decode_token(token)
        if payload and "sub" in payload:
            try:
                set_current_user_id(int(payload["sub"]))
            except (ValueError, TypeError):
                pass

    response = await call_next(request)
    return response
