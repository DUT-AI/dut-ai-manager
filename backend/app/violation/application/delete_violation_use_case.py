from fastapi import HTTPException

from app.violation.infrastructure.repository import ViolationRepository


class DeleteViolationUseCase:
    """Soft-delete a violation."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def execute(self, item_id: int) -> bool:
        existing = self.repo.get_by_id(item_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Violation not found")
        return self.repo.delete_by_id(item_id)
