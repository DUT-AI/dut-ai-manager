from app.permission_request.application.strategies.base import PermissionStrategy
from app.permission_request.domain.payloads import (
    AbsencePayload,
    ChangeMeetingPayload,
    LatePayload,
    OtherPayload,
    PostponePayload,
)
from app.permission_request.domain.value_objects import RequestCategory

type StrategyInstance = (
    PermissionStrategy[AbsencePayload]
    | PermissionStrategy[LatePayload]
    | PermissionStrategy[PostponePayload]
    | PermissionStrategy[ChangeMeetingPayload]
    | PermissionStrategy[OtherPayload]
)


class PermissionStrategyRegistry:
    """Registry pattern holding strategy instances keyed by RequestCategory."""

    def __init__(self, strategies: list[StrategyInstance]) -> None:
        self._strategies: dict[RequestCategory, StrategyInstance] = {}
        for strategy in strategies:
            self._strategies[strategy.category] = strategy

    def get(self, category: RequestCategory) -> StrategyInstance:
        strategy = self._strategies.get(category)
        if not strategy:
            raise ValueError(
                f"No permission strategy registered for category: {category}"
            )
        return strategy
