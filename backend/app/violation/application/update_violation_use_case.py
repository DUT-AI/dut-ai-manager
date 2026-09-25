from datetime import datetime

from app.violation.domain.entity import Violation
from app.violation.infrastructure.repository import ViolationRepository


class UpdateViolationUseCase:
    """Update an existing violation."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def execute(
        self, item_id: int, reason: str | None = None, date: datetime | None = None
    ) -> Violation | None:
        existing = self.repo.get_by_id(item_id)
        if not existing:
            return None

        # Build updated entity — Pydantic validates on creation
        updated = existing.model_copy(
            update={
                k: v
                for k, v in {"reason": reason, "date": date}.items()
                if v is not None
            }
        )
        return self.repo.update(updated)
