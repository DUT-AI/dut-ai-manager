from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, List, Optional, Union

from sqlalchemy import and_, or_
from app.core.queries.query_support.exceptions import PaginationError


@dataclass(frozen=True, slots=True, kw_only=True)
class OffsetPaginationParams:
    MAX_INT32: ClassVar[int] = 2**31 - 1

    limit: int
    offset: int

    def __post_init__(self) -> None:
        self._validate(limit=self.limit, offset=self.offset)

    @classmethod
    def _validate(cls, limit: int, offset: int) -> None:
        if limit <= 0:
            raise PaginationError(f"Limit must be greater than 0, got {limit}")
        if limit > cls.MAX_INT32:
            raise PaginationError(f"Limit cannot be greater than {cls.MAX_INT32}, got {limit}")
        if offset < 0:
            raise PaginationError(f"Offset must be non-negative, got {offset}")
        if offset > cls.MAX_INT32:
            raise PaginationError(f"Offset cannot be greater than {cls.MAX_INT32}, got {offset}")


class SortingOrder(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True, slots=True, kw_only=True)
class SortingParams:
    field: str
    order: SortingOrder


class FilterOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    LIKE = "like"
    IN = "in"
    IS_NULL = "is_null"
    MONTH_EQ = "month_eq"
    YEAR_EQ = "year_eq"


class LogicOperator(StrEnum):
    AND = "AND"
    OR = "OR"


@dataclass(frozen=True, slots=True, kw_only=True)
class FilterCriterion:
    field: str
    operator: FilterOperator
    value: Any = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FilterGroup:
    logic: LogicOperator
    elements: List[Union[FilterCriterion, "FilterGroup"]]


@dataclass(frozen=True, slots=True, kw_only=True)
class QuerySupport:
    pagination: Optional[OffsetPaginationParams] = None
    sorting: Optional[List[SortingParams]] = None
    filters: Optional[Union[FilterGroup, FilterCriterion]] = None
    include: Optional[List[str]] = None


def _apply_filters(model: Any, group: FilterGroup) -> Any:
    """Recursively convert FilterGroup to SQLAlchemy clauses."""
    clauses = []
    for element in group.elements:
        if isinstance(element, FilterGroup):
            clauses.append(_apply_filters(model, element))
        else:
            col = getattr(model, element.field)
            op = element.operator
            val = element.value

            if op == FilterOperator.EQ:
                clauses.append(col == val)
            elif op == FilterOperator.NE:
                clauses.append(col != val)
            elif op == FilterOperator.GT:
                clauses.append(col > val)
            elif op == FilterOperator.LT:
                clauses.append(col < val)
            elif op == FilterOperator.GTE:
                clauses.append(col >= val)
            elif op == FilterOperator.LTE:
                clauses.append(col <= val)
            elif op == FilterOperator.LIKE:
                clauses.append(col.like(f"%{val}%"))
            elif op == FilterOperator.IN:
                clauses.append(col.in_(val))
            elif op == FilterOperator.IS_NULL:
                clauses.append(col.is_(None))
            elif op == FilterOperator.MONTH_EQ:
                from sqlalchemy import extract
                clauses.append(extract("month", col) == val)
            elif op == FilterOperator.YEAR_EQ:
                from sqlalchemy import extract
                clauses.append(extract("year", col) == val)

    if not clauses:
        return True

    if group.logic == LogicOperator.OR:
        return or_(*clauses)
    return and_(*clauses)


def apply_query_support(stmt: Any, model: Any, support: QuerySupport) -> Any:
    """Apply filters, sorting, pagination and eager loading to a statement."""
    from sqlalchemy.orm import joinedload

    # 1. Eager Loading (Include)
    if support.include:
        for relation_path in support.include:
            parts = relation_path.split(".")
            current_option = None
            current_model = model

            for part in parts:
                rel = getattr(current_model, part)
                if current_option is None:
                    current_option = joinedload(rel)
                else:
                    current_option = current_option.joinedload(rel)

                # Update current_model for next part
                if hasattr(rel, "property") and hasattr(rel.property, "mapper"):
                    current_model = rel.property.mapper.class_

            if current_option:
                stmt = stmt.options(current_option)

    # 2. Filters
    if support.filters:
        if isinstance(support.filters, FilterCriterion):
            # Convert single criterion to a group automatically
            group = FilterGroup(logic=LogicOperator.AND, elements=[support.filters])
            stmt = stmt.where(_apply_filters(model, group))
        else:
            stmt = stmt.where(_apply_filters(model, support.filters))

    if support.sorting:
        for s in support.sorting:
            col = getattr(model, s.field)
            if s.order == SortingOrder.DESC:
                stmt = stmt.order_by(col.desc())
            else:
                stmt = stmt.order_by(col.asc())

    if support.pagination:
        stmt = stmt.offset(support.pagination.offset).limit(support.pagination.limit)

    return stmt