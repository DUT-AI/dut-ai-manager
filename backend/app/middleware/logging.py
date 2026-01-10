import time
from fastapi import Request
from loguru import logger
from app.core.context import get_current_user_id


async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Get user ID from context
    user_id = get_current_user_id() or "Anonymous"

    # Prepare request info
    method = request.method
    path = request.url.path
    query = request.url.query

    # Try to get body
    body = ""
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = body_bytes.decode("utf-8")

                async def receive():
                    return {"type": "http.request", "body": body_bytes}

                request._receive = receive
        except Exception:  # pylint: disable=broad-exception-caught
            body = "<Could not read body>"

    logger.info(
        f"Request: {method} {path}{'?' + query if query else ''} | User: {user_id} | Body: {body[:500]}..."
    )

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    status_code = response.status_code

    logger.info(
        f"Response: {method} {path} | Status: {status_code} | Time: {process_time:.2f}ms"
    )

    return response
