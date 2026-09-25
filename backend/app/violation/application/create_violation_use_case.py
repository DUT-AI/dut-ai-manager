from datetime import datetime
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
