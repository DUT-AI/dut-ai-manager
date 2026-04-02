from typing import Optional, List, Any, cast, Union
from app.shared.domain.query_support import (
    QuerySupport, 
    OffsetPaginationParams, 
    SortingParams, 
    SortingOrder,
    FilterGroup, 
    FilterCriterion,
    LogicOperator
)

def build_query_support(
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    descending: bool = True,
    filters: Optional[List[FilterCriterion]] = None,
    filter_group: Optional[FilterGroup] = None,
    include: Optional[List[str]] = None
) -> QuerySupport:
    """
    Helper to build QuerySupport from common parameters.
    """
    pagination = OffsetPaginationParams(limit=limit, offset=skip)

    sorting = None
    if sort_by:
        order = SortingOrder.DESC if descending else SortingOrder.ASC
        sorting = [SortingParams(field=sort_by, order=order)]

    final_filter = filter_group
    if filters and not final_filter:
        final_filter = FilterGroup(elements=cast(List[Union[FilterCriterion, FilterGroup]], filters), logic=LogicOperator.AND)
    elif filters and final_filter:
        # If both are provided, combine them (AND by default)
        combined_elements = list(final_filter.elements) + cast(List[Union[FilterCriterion, FilterGroup]], list(filters))
        final_filter = FilterGroup(elements=combined_elements, logic=LogicOperator.AND)

    return QuerySupport(
        pagination=pagination,
        sorting=sorting,
        filters=final_filter,
        include=include
    )
