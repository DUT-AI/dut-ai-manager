"""
API Tests for Auth Controller (/api/v1/auth).
Focus on /auth/me endpoint with database query via user_repo.
"""

import pytest


def test_get_me_success(admin_client):
    """Khi user đăng nhập, GET /auth/me query CSDL và trả về đầy đủ UserReponseMe."""
    res = admin_client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    user_data = data["data"]
    assert user_data["id"] is not None
    assert "name" in user_data
    assert "email" in user_data
    assert "status" in user_data
    assert "is_deleted" in user_data
    assert "role_names" in user_data
    assert "permissions" in user_data


def test_get_me_unauthenticated(unauth_client):
    """Chưa đăng nhập gọi /auth/me phải trả về 401."""
    res = unauth_client.get("/api/v1/auth/me")
    assert res.status_code == 401
