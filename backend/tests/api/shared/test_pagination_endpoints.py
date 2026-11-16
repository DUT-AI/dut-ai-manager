"""
Integration Tests for Unified Pagination Endpoints (/api/v1/...).
Validates page and page_size query parameters, response pagination envelope metadata,
and specialized calendar / options endpoints.
"""


def test_users_pagination_endpoint(admin_client):
    """GET /api/v1/users with page and page_size returns pagination metadata."""
    res = admin_client.get("/api/v1/users?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 2
    assert "pagination" in data
    assert data["pagination"] is not None
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2
    assert "total" in data["pagination"]
    assert "total_pages" in data["pagination"]
    assert "has_next" in data["pagination"]


def test_users_options_endpoint_has_no_pagination(admin_client):
    """GET /api/v1/users/options returns list of users without pagination metadata."""
    res = admin_client.get("/api/v1/users/options")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert data.get("pagination") is None


def test_teams_options_endpoint_has_no_pagination(admin_client):
    """GET /api/v1/teams/options returns list of teams without pagination metadata."""
    res = admin_client.get("/api/v1/teams/options")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert data.get("pagination") is None


def test_violations_pagination_endpoint(admin_client):
    """GET /api/v1/violations with page and page_size returns pagination metadata."""
    res = admin_client.get("/api/v1/violations?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 5
    assert "pagination" in data
    assert data["pagination"] is not None
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 5


def test_meetings_pagination_endpoint(admin_client):
    """GET /api/v1/meetings with page and page_size returns pagination metadata."""
    res = admin_client.get("/api/v1/meetings?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 5
    assert "pagination" in data
    assert data["pagination"] is not None
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 5


def test_meetings_calendar_view_bypasses_pagination(admin_client):
    """GET /api/v1/meetings with start_date and end_date returns all meetings without pagination."""
    res = admin_client.get("/api/v1/meetings?start_date=2026-01-01&end_date=2026-12-31")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert data.get("pagination") is None


def test_homeworks_pagination_endpoint(admin_client):
    """GET /api/v1/homeworks with page and page_size returns pagination metadata."""
    res = admin_client.get("/api/v1/homeworks?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 5
    assert "pagination" in data
    assert data["pagination"] is not None
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 5
