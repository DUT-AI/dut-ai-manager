import contextvars

from dishka import AsyncContainer

_request_container_context: contextvars.ContextVar[AsyncContainer | None] = (
    contextvars.ContextVar("request_container_context", default=None)
)


def set_request_container(container: AsyncContainer):
    return _request_container_context.set(container)


def get_request_container() -> AsyncContainer | None:
    return _request_container_context.get()
