"""
Integration tests for Permission Requests and Expenses pagination endpoints.
Verifies that endpoints strictly use PaginationParams (page, page_size)
and return ApiResponse with PaginationMeta.
"""


def test_get_permission_requests_pagination(admin_client):
    """Kiểm tra phân trang danh sách đơn xin phép qua API."""
    res = admin_client.get("/api/v1/permissions?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10
    assert "total" in data["pagination"]
    assert "total_pages" in data["pagination"]


def test_get_expenses_pagination(admin_client):
    """Kiểm tra phân trang danh sách chi tiêu qua API."""
    res = admin_client.get("/api/v1/expenses/?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10
    assert "total" in data["pagination"]
    assert "total_pages" in data["pagination"]
