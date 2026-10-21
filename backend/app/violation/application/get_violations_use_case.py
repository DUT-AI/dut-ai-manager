from datetime import date, datetime, time

from fastapi import HTTPException

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.violation.domain.entity import Violation
from app.violation.infrastructure.repository import ViolationRepository


class GetViolationsUseCase:
    """Query violations with various filters."""

    def __init__(self, repo: ViolationRepository):
        self.repo = repo

    def get_paged(
        self,
        page: int = 1,
        page_size: int = 20,
        deleted: bool = False,
        user_id: int | None = None,
        month: int | None = None,
        year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[list[Violation], int]:
        filters = []
        if user_id:
            filters.append(
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user_id
                )
            )
        if month:
            filters.append(
                FilterCriterion(
                    field="created_at", operator=FilterOperator.MONTH_EQ, value=month
                )
            )
        if year:
            filters.append(
                FilterCriterion(
                    field="created_at", operator=FilterOperator.YEAR_EQ, value=year
                )
            )
        if start_date:
            filters.append(
                FilterCriterion(
                    field="created_at",
                    operator=FilterOperator.GTE,
                    value=datetime.combine(start_date, time.min),
                )
            )
        if end_date:
            filters.append(
                FilterCriterion(
                    field="created_at",
                    operator=FilterOperator.LTE,
                    value=datetime.combine(end_date, time.max),
                )
            )

        qs = build_query_support(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by="created_at",
            descending=True,
        )
        return self.repo.get_paged(query_support=qs, deleted=deleted)

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
