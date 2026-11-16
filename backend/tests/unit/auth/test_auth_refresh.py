"""
Unit & Integration Tests for Auth Refresh (/api/v1/auth/refresh).
Verifies HTTP 200 on valid refresh token and HTTP 401 on missing/expired/invalid tokens.
"""

from fastapi.testclient import TestClient

from app.auth.domain.token_service import TokenService
from app.user.domain.entity import UserEntity


def test_refresh_token_success_via_cookie(unauth_client: TestClient, mock_current_user: UserEntity):
    """Khi có cookie refresh_token hợp lệ, POST /auth/refresh trả về 200 và cấp token mới."""
    _, refresh_token = TokenService.create_tokens(mock_current_user)

    unauth_client.cookies.set("refresh_token", refresh_token)
    response = unauth_client.post("/api/v1/auth/refresh", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["is_success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

    # Kiểm tra cookie mới được set
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


def test_refresh_token_success_via_body(unauth_client: TestClient, mock_current_user: UserEntity):
    """Khi gửi refresh_token qua body JSON, POST /auth/refresh trả về 200 và cấp token mới."""
    _, refresh_token = TokenService.create_tokens(mock_current_user)

    response = unauth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert data["is_success"] is True
    assert data["data"]["access_token"] is not None
    assert data["data"]["refresh_token"] is not None


def test_refresh_token_missing_raises_401(unauth_client: TestClient):
    """Khi thiếu refresh_token trong cả cookie và body, trả về 401 Unauthorized."""
    response = unauth_client.post("/api/v1/auth/refresh", json={})

    assert response.status_code == 401
    data = response.json()
    assert data["is_success"] is False
    assert "missing" in data["message"].lower() or "refresh token" in data["message"].lower()


def test_refresh_token_invalid_or_expired_raises_401(unauth_client: TestClient):
    """Khi refresh_token không hợp lệ hoặc hết hạn, trả về 401 Unauthorized."""
    response = unauth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.jwt.token"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["is_success"] is False


def test_refresh_token_inactive_user_raises_401(unauth_client: TestClient, db_session):
    """Khi user bị khóa hoặc inactive, POST /auth/refresh trả về 401."""
    import uuid

    from app.user.domain.entity import UserStatus
    from app.user.infrastructure.model import UserModel

    unique_email = f"inactive_{uuid.uuid4().hex[:8]}@example.com"
    user = UserModel(
        name="Inactive Test User",
        email=unique_email,
        status=UserStatus.INACTIVE.value,
        is_deleted=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    user_entity = user.to_entity()
    _, refresh_token = TokenService.create_tokens(user_entity)

    response = unauth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["is_success"] is False
    assert "inactive" in data["message"].lower() or "not found" in data["message"].lower()
