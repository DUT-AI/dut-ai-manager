"""
Pagination dependencies and value objects.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

TEntity = TypeVar("TEntity")


class PaginationParams(BaseModel):
    """
    FastAPI Query Dependency for pagination parameters.
    Default page_size: 20 per Constitution Principle VIII.
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Items per page (default 20, max 100)",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass(frozen=True, slots=True)
class PagedResult(Generic[TEntity]):
    """Value object holding paginated entities and total count."""

    items: list[TEntity]
    total: int
    page: int
    page_size: int
