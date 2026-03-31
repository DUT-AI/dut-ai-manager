import pytest
from app.auth.domain.auth_user_entity import AuthUser
from app.user.domain.value_objects import UserStatus


def test_auth_user_creation():
    user = AuthUser(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        status=UserStatus.ACTIVE,
    )
    assert user.id == 1
    assert user.email == "test@example.com"
    assert user.is_active() is True


def test_auth_user_inactive():
    user = AuthUser(
        id=2,
        email="inactive@example.com",
        hashed_password="hashed_password",
        status=UserStatus.INACTIVE,
    )
    assert user.is_active() is False
