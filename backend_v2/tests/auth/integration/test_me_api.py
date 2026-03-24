import pytest
import jwt
from fastapi.testclient import TestClient
from app.infrastructure.FastAPI.server import create_app
from app.settings import JWTSetting
from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.fastapi import setup_dishka
from app.auth.infrastructure.jwt_service import JwtTokenService
from app.auth.domain.interfaces import ITokenService

# Chúng ta cần một secret cố định để viết test
TEST_SECRET = "test_secret_key_for_integration_testing_12345"

class AuthTestProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_jwt_settings(self) -> JWTSetting:
        settings = JWTSetting()
        settings.SECRET_KEY = TEST_SECRET
        return settings

    @provide(scope=Scope.APP)
    def provide_token_service(self, settings: JWTSetting) -> ITokenService:
        return JwtTokenService(settings)

@pytest.fixture
def test_client():
    # Tạo app mới để tránh lỗi "Cannot add middleware after an application has started"
    app = create_app()
    # Thiết lập container mock cho test
    container = make_async_container(AuthTestProvider())
    setup_dishka(container, app)
    return TestClient(app)

def test_get_me_success_from_jwt_claims(test_client):
    """
    Kịch bản: Người dùng đã login và có JWT hợp lệ.
    Kỳ vọng: API /me trả về đúng thông tin trích xuất từ JWT mà không lỗi.
    """
    payload = {
        "sub": "123",
        "email": "test@example.com",
        "name": "Test User",
        "role": "admin",
        "avatar": "https://example.com/avatar.png",
        "permissions": ["user:read", "user:write"]
    }
    # Tạo token với secret của test
    token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
    
    response = test_client.get(
        "/auth/me", 
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["id"] == 123
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["role_name"] == "admin"
    assert data["avatar_url"] == "https://example.com/avatar.png"
    assert data["permissions"] == ["user:read", "user:write"]

def test_get_me_unauthorized(test_client):
    """
    Kịch bản: Không gửi header Authorization.
    Kỳ vọng: Trả về 401.
    """
    response = test_client.get("/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["message"]

def test_get_me_invalid_token(test_client):
    """
    Kịch bản: Gửi token sai secret hoặc định dạng.
    Kỳ vọng: Trả về 401.
    """
    response = test_client.get(
        "/auth/me", 
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["message"]
