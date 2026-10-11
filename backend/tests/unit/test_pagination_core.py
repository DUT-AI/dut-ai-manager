"""
Unit tests for core pagination classes:
- PaginationMeta (Response DTO)
- PaginationParams (Request Dependency)
- OffsetPaginationParams (Domain)
- BaseRepository.get_paged
"""

import pytest
from pydantic import ValidationError

from app.shared.application.pagination import PaginationParams
from app.shared.application.response import ApiResponse, PaginationMeta
from app.shared.domain.query_support import OffsetPaginationParams


def test_pagination_meta_creation():
    """Test PaginationMeta calculations and flags."""
    # Exact division
    meta = PaginationMeta.create(page=1, page_size=20, total=40)
    assert meta.page == 1
    assert meta.page_size == 20
    assert meta.total == 40
    assert meta.total_pages == 2
    assert meta.has_next is True

    # Last page
    meta_last = PaginationMeta.create(page=2, page_size=20, total=40)
    assert meta_last.page == 2
    assert meta_last.total_pages == 2
    assert meta_last.has_next is False

    # Partial page (e.g. 45 items -> 3 pages)
    meta_partial = PaginationMeta.create(page=2, page_size=20, total=45)
    assert meta_partial.total_pages == 3
    assert meta_partial.has_next is True

    # Zero items
    meta_zero = PaginationMeta.create(page=1, page_size=20, total=0)
    assert meta_zero.total == 0
    assert meta_zero.total_pages == 0
    assert meta_zero.has_next is False


def test_api_response_with_pagination():
    """Test ApiResponse envelope with optional pagination."""
    meta = PaginationMeta.create(page=1, page_size=20, total=10)
    items = [{"id": 1, "name": "Item 1"}]

    resp = ApiResponse.success(data=items, message="OK", pagination=meta)
    assert resp.is_success is True
    assert resp.status_code == 200
    assert resp.data == items
    assert resp.pagination is not None
    assert resp.pagination.total == 10
    assert resp.pagination.page == 1

    # Unpaginated response backwards compatibility
    resp_unpaginated = ApiResponse.success(data=items)
    assert resp_unpaginated.pagination is None


def test_pagination_params_validation():
    """Test FastAPI query dependency PaginationParams."""
    # Default values
    p = PaginationParams()
    assert p.page == 1
    assert p.page_size == 20
    assert p.offset == 0
    assert p.limit == 20

    # Custom valid values
    p_custom = PaginationParams(page=3, page_size=50)
    assert p_custom.page == 3
    assert p_custom.page_size == 50
    assert p_custom.offset == 100
    assert p_custom.limit == 50

    # Invalid page (< 1)
    with pytest.raises(ValidationError):
        PaginationParams(page=0)

    # Invalid page_size (> 100)
    with pytest.raises(ValidationError):
        PaginationParams(page_size=101)


def test_offset_pagination_params_from_page():
    """Test OffsetPaginationParams.from_page factory method."""
    params = OffsetPaginationParams.from_page(page=1, page_size=20)
    assert params.limit == 20
    assert params.offset == 0

    params_page_3 = OffsetPaginationParams.from_page(page=3, page_size=25)
    assert params_page_3.limit == 25
    assert params_page_3.offset == 50
