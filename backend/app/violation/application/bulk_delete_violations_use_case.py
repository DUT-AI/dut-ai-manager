from app.violation.infrastructure.repository import ViolationRepository


class BulkDeleteViolationsUseCase:
    """Soft-delete multiple violations by IDs."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def execute(self, ids: list[int]) -> int:
        if not ids:
            return 0
        return self.repo.bulk_delete(ids)
