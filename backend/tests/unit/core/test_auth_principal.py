import pytest
from app.core.principal import AuthPrincipal, PrincipalType
from app.shared.application.response import BadRequestException


def test_auth_principal_user_creation():
    principal = AuthPrincipal(
        actor_id=10,
        actor_type=PrincipalType.USER,
        name="John Doe",
        email="john@example.com",
        role_names=["MEMBER"],
        permissions={"homework.read", "meeting.read"},
    )

    assert principal.is_user is True
    assert principal.is_api_key is False
    assert principal.actor_id == 10
    assert principal.user_id == 10
    assert principal.name == "John Doe"
    assert principal.email == "john@example.com"
    assert principal.has_permission("homework.read") is True
    assert principal.has_permission("homework.create") is False


def test_auth_principal_admin_bypass():
    admin_principal = AuthPrincipal(
        actor_id=1,
        actor_type=PrincipalType.USER,
        name="Admin User",
        email="admin@example.com",
        role_names=["ADMIN"],
        permissions=set(),
    )

    assert admin_principal.is_user is True
    assert admin_principal.has_permission("any.permission") is True
    assert admin_principal.has_permission("homework.delete") is True


def test_auth_principal_api_key():
    api_key_principal = AuthPrincipal(
        actor_id=5,
        actor_type=PrincipalType.API_KEY,
        name="System: Scanner Bot",
        role_names=["SYSTEM"],
        permissions={"homework.read"},
    )

    assert api_key_principal.is_user is False
    assert api_key_principal.is_api_key is True
    assert api_key_principal.has_permission("homework.read") is True
    assert api_key_principal.has_permission("homework.create") is False

    # Calling user_id on an API Key must raise 403 Forbidden
    with pytest.raises(BadRequestException) as exc_info:
        _ = api_key_principal.user_id

    assert exc_info.value.status_code == 403
