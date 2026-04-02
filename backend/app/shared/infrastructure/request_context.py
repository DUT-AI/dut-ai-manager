import contextvars
from dishka import AsyncContainer
from typing import Optional

_request_container_context: contextvars.ContextVar[Optional[AsyncContainer]] = contextvars.ContextVar(
    "request_container_context", default=None
)

def set_request_container(container: AsyncContainer):
    return _request_container_context.set(container)

def get_request_container() -> Optional[AsyncContainer]:
    return _request_container_context.get()
