"""
Violation Use Cases — application layer.

Each use case represents one business operation.
Use cases orchestrate: repository + domain logic + events.
"""

from datetime import datetime

from fastapi import HTTPException
from loguru import logger

from app.shared.domain.event_bus import EventBus
from app.violation.domain.entity import Violation
from app.violation.domain.events import ViolationCreated
from app.violation.infrastructure.repository import ViolationRepository


class CreateViolationUseCase:
    """Create violations for one or more users."""

    def __init__(self, repo: ViolationRepository, event_bus: type[EventBus] = EventBus):
        self.repo = repo
        self.event_bus = event_bus

    async def execute(
        self,
        user_ids: list[int],
        reason: str,
        date: datetime,
        is_system: bool = False,
        system_user_id: int | None = None,
    ) -> list[Violation]:
        violations_to_create: list[Violation] = []

        for user_id in user_ids:
            if is_system:
                # Check for existing violations to prevent duplicates from recurrent job runs
                existing = self.repo.get_by_user_and_date(user_id, date)
                if any(v.reason == reason for v in existing):
                    continue

                violation = Violation.create_system_violation(
                    user_id=user_id,
                    reason=reason,
                    date=date,
                    system_user_id=system_user_id,
                )
            else:
                violation = Violation(user_id=user_id, reason=reason, date=date)
            violations_to_create.append(violation)

        if not violations_to_create:
            return []

        # Batch save violations
        saved_violations = self.repo.save_all(violations_to_create)

        # Publish domain events for all saved violations
        for saved in saved_violations:
            logger.debug(f"Created violation id={saved.id} for user_id={saved.user_id}")
            assert saved.id is not None
            await self.event_bus.publish(
                ViolationCreated(
                    violation_id=saved.id,
                    user_id=saved.user_id,
                    reason=saved.reason,
                    date=saved.date.isoformat() if saved.date else "",
                    user_name=saved.owner.name if saved.owner else None,
                    creator_name=saved.creator.name if saved.creator else None,
                )
            )

        return saved_violations


class GetViolationsUseCase:
    """Query violations with various filters."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[Violation]:
        return self.repo.get_all(skip=skip, limit=limit, deleted=deleted)

    def get_by_month(
        self, month: int | None, year: int | None, user_id: int | None = None
    ) -> list[Violation]:
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year

        return self.repo.get_by_month(month=month, year=year, user_id=user_id)

    def get_by_id(self, item_id: int) -> Violation:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Violation not found")
        return item

    def get_by_user_and_date(self, user_id: int, target_date) -> list[Violation]:
        return self.repo.get_by_user_and_date(user_id, target_date)

    def get_by_date(self, target_date) -> list[Violation]:
        return self.repo.get_by_date(target_date)


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


class DeleteViolationUseCase:
    """Soft-delete a violation."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def execute(self, item_id: int) -> bool:
        existing = self.repo.get_by_id(item_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Violation not found")
        return self.repo.delete_by_id(item_id)


class RestoreViolationUseCase:
    """Restore a soft-deleted violation."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def execute(self, item_id: int) -> Violation | None:
        dummy = Violation.model_construct(id=item_id)
        return self.repo.restore(dummy)
