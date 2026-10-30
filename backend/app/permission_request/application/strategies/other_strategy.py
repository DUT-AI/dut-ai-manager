from app.permission_request.application.strategies.base import PermissionStrategy
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.payloads import OtherPayload
from app.permission_request.domain.value_objects import RequestCategory


class OtherStrategy(PermissionStrategy[OtherPayload]):
    """Strategy for generic / uncategorized permission requests."""

    @property
    def category(self) -> RequestCategory:
        return RequestCategory.OTHER

    def validate(self, request: PermissionRequest[OtherPayload]) -> None:
        pass

    async def on_created(
        self,
        request: PermissionRequest[OtherPayload],
        user_id: int,
    ) -> None:
        pass

    def on_deleted(
        self,
        request: PermissionRequest[OtherPayload],
        user_id: int,
    ) -> None:
        pass
