from datetime import date

from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.domain.value_objects import BonusPointType
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator


class GetBonusPointsUseCase:
    def __init__(self, repository: BonusPointRepository):
        self.repository = repository

    def execute(
        self,
        user_id: int | None = None,
        type: BonusPointType | None = None,
        month: int | None = None,
        year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
        deleted: bool = False,
    ) -> tuple[list[BonusPoint], int]:
        filters = []
        if user_id:
            filters.append(
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user_id
                )
            )
        if type:
            type_val = type.value if hasattr(type, "value") else str(type)
            filters.append(
                FilterCriterion(
                    field="type", operator=FilterOperator.EQ, value=type_val
                )
            )
        if start_date:
            filters.append(
                FilterCriterion(
                    field="date", operator=FilterOperator.GTE, value=start_date
                )
            )
        if end_date:
            filters.append(
                FilterCriterion(
                    field="date", operator=FilterOperator.LTE, value=end_date
                )
            )
        if month:
            filters.append(
                FilterCriterion(
                    field="date", operator=FilterOperator.MONTH_EQ, value=month
                )
            )
        if year:
            filters.append(
                FilterCriterion(
                    field="date", operator=FilterOperator.YEAR_EQ, value=year
                )
            )

        qs = build_query_support(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by="created_at",
            descending=True,
        )
        return self.repository.get_paged(query_support=qs, deleted=deleted)
