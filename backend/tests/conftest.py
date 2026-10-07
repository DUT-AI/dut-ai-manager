"""
Pytest configuration and shared fixtures for unit, integration, and api test suites.
"""

from typing import Generator
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient

from app.core.config import settings
from app.core.deps import get_current_user
from app.main import create_app
from app.user.domain.entity import UserEntity, UserStatus


@pytest.fixture(scope="session")
def db_engine():
    """Engine kết nối tới cơ sở dữ liệu được cấu hình trong settings."""
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    return engine


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """Session factory cho DB."""
    return sessionmaker(bind=db_engine, autocommit=False, autoflush=False)


@pytest.fixture
def db_session(db_session_factory) -> Generator[Session, None, None]:
    """
    Session database cho từng test case.
    Tự động rollback khi kết thúc test để đảm bảo không làm bẩn dữ liệu.
    """
    session = db_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_current_user(db_engine) -> UserEntity:
    """Lấy một User thật từ DB hoặc tạo mock entity có quyền Admin mặc định."""
    with db_engine.connect() as conn:
        user_row = conn.execute(
            text("SELECT id, name, email FROM users WHERE is_deleted = false LIMIT 1")
        ).fetchone()

    user_id = user_row[0] if user_row else 999
    user_name = user_row[1] if user_row else "Admin User"
    user_email = user_row[2] if user_row else "admin@example.com"

    return UserEntity(
        id=user_id,
        name=user_name,
        email=user_email,
        status=UserStatus.ACTIVE,
        role_names=["admin"],
    )


@pytest.fixture
def member_user(mock_current_user) -> UserEntity:
    """User thành viên bình thường, không có role admin hoặc quyền đặc biệt."""
    return UserEntity(
        id=mock_current_user.id,
        name=mock_current_user.name,
        email=mock_current_user.email,
        status=UserStatus.ACTIVE,
        role_names=["member"],
        permissions=set(),
    )


@pytest.fixture
def api_client(mock_current_user) -> Generator[TestClient, None, None]:
    """TestClient gọi API FastAPI với quyền Admin."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(api_client) -> TestClient:
    """Alias cho api_client có quyền Admin."""
    return api_client


@pytest.fixture
def member_client(member_user) -> Generator[TestClient, None, None]:
    """TestClient gọi API với quyền Member bình thường (để kiểm thử 403 Forbidden)."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: member_user
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client() -> Generator[TestClient, None, None]:
    """TestClient không đăng nhập (để kiểm thử 401 Unauthorized)."""
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    yield client
