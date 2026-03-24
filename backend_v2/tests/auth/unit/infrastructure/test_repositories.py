import pytest
from app.auth.infrastructure.jwt_service import JwtTokenService
from app.auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher
from app.settings import JWTSetting

@pytest.fixture
def jwt_settings():
    return JWTSetting(
        JWT_SECRET_KEY="test_secret",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        REFRESH_TOKEN_EXPIRE_MINUTES=60 * 24 * 7
    )

@pytest.fixture
def jwt_service(jwt_settings):
    return JwtTokenService(jwt_settings)

def test_jwt_create_and_decode(jwt_service):
    payload = {"sub": "1", "name": "Test User"}
    token = jwt_service.create_access_token(payload)
    
    decoded = jwt_service.decode_token(token)
    assert decoded["sub"] == "1"
    assert decoded["name"] == "Test User"

def test_password_hasher():
    hasher = BcryptPasswordHasher()
    password = "secret_password"
    hashed = hasher.hash(password)
    
    assert hasher.verify(password, hashed) is True
    assert hasher.verify("wrong_password", hashed) is False
