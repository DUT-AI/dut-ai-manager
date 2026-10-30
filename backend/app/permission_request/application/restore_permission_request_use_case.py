from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.infrastructure.repository import PermissionRequestRepository


class RestorePermissionRequestUseCase:
    """Khôi phục yêu cầu xin phép"""

    def __init__(self, repo: PermissionRequestRepository):
        self.repo = repo

    def execute(self, request_id: int) -> PermissionRequest | None:
        dummy = PermissionRequest.model_construct(id=request_id)
        return self.repo.restore(dummy)
