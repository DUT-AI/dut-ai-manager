from datetime import date, datetime
from fastapi import HTTPException

from app.violation.domain.entity import Violation
from app.violation.infrastructure.repository import ViolationRepository


class GetViolationsUseCase:
    """Query violations with various filters."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[Violation]:
        return self.repo.get_all(skip=skip, limit=limit, deleted=deleted)

    def get_by_month(
        self,
        month: int | None = None,
        year: int | None = None,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Violation]:
        if not month and not year and not start_date and not end_date and not user_id:
            month = datetime.now().month
            year = datetime.now().year

        return self.repo.get_by_month(
            month=month,
            year=year,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_by_id(self, item_id: int) -> Violation:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Violation not found")
        return item

    def get_by_user_and_date(self, user_id: int, target_date) -> list[Violation]:
        return self.repo.get_by_user_and_date(user_id, target_date)

    def get_by_date(self, target_date) -> list[Violation]:
        return self.repo.get_by_date(target_date)
