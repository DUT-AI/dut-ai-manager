from app.violation.domain.entity import Violation
from app.violation.infrastructure.repository import ViolationRepository


class RestoreViolationUseCase:
    """Restore a soft-deleted violation."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def execute(self, item_id: int) -> Violation | None:
        dummy = Violation.model_construct(id=item_id)
        return self.repo.restore(dummy)
