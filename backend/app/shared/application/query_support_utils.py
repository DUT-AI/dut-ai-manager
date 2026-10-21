from typing import cast

from app.shared.domain.query_support import (
    FilterCriterion,
    FilterGroup,
    LogicOperator,
    OffsetPaginationParams,
    QuerySupport,
    SortingOrder,
    SortingParams,
)


def build_query_support(
    skip: int | None = None,
    limit: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort_by: str | None = None,
    descending: bool = True,
    filters: list[FilterCriterion] | None = None,
    filter_group: FilterGroup | None = None,
    include: list[str] | None = None,
) -> QuerySupport:
    """
    Helper to build QuerySupport from common parameters.
    Supports both (page, page_size) and legacy (skip, limit).
    """
    if page is not None and page_size is not None:
        pagination = OffsetPaginationParams.from_page(page=page, page_size=page_size)
    elif limit is not None:
        pagination = OffsetPaginationParams(limit=limit, offset=skip or 0)
    elif page_size is not None:
        pagination = OffsetPaginationParams.from_page(
            page=page or 1, page_size=page_size
        )
    else:
        pagination = OffsetPaginationParams(limit=100, offset=skip or 0)

    sorting = None
    if sort_by:
        order = SortingOrder.DESC if descending else SortingOrder.ASC
        sorting = [SortingParams(field=sort_by, order=order)]

    final_filter = filter_group
    if filters and not final_filter:
        final_filter = FilterGroup(
            elements=cast(list[FilterCriterion | FilterGroup], filters),
            logic=LogicOperator.AND,
        )
    elif filters and final_filter:
        # If both are provided, combine them (AND by default)
        combined_elements = list(final_filter.elements) + cast(
            list[FilterCriterion | FilterGroup], list(filters)
        )
        final_filter = FilterGroup(elements=combined_elements, logic=LogicOperator.AND)

    return QuerySupport(
        pagination=pagination, sorting=sorting, filters=final_filter, include=include
    )
