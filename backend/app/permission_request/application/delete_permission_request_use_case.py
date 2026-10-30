from app.permission_request.application.strategies.registry import (
    PermissionStrategyRegistry,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository


class DeletePermissionRequestUseCase:
    """Xóa yêu cầu xin phép (ủy quyền dọn dẹp cho Strategy)."""

    def __init__(
        self,
        repo: PermissionRequestRepository,
        strategy_registry: PermissionStrategyRegistry,
    ):
        self.repo = repo
        self.strategy_registry = strategy_registry

    def execute(self, request_id: int) -> bool:
        entity = self.repo.get_by_id(request_id)
        if entity and entity.user_id:
            try:
                strategy = self.strategy_registry.get(entity.category)
                strategy.on_deleted(entity, entity.user_id)
            except Exception:
                pass
        return self.repo.delete(request_id)
