from unittest.mock import MagicMock

import pytest
from fastapi import status

from app.core.deps import PermissionChecker, get_current_principal
from app.core.principal import AuthPrincipal, PrincipalType
from app.shared.application.response import BadRequestException


def test_permission_checker_success():
    principal = AuthPrincipal(
        actor_id=1,
        actor_type=PrincipalType.USER,
        name="User 1",
        role_names=["MEMBER"],
        permissions={"homework.read"},
    )

    checker = PermissionChecker("homework.read")
    result = checker(principal)
    assert result == principal


def test_permission_checker_missing_permission():
    principal = AuthPrincipal(
        actor_id=1,
        actor_type=PrincipalType.USER,
        name="User 1",
        role_names=["MEMBER"],
        permissions={"homework.read"},
    )

    checker = PermissionChecker("homework.delete")
    with pytest.raises(BadRequestException) as exc_info:
        checker(principal)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "homework.delete" in exc_info.value.message


def test_permission_checker_admin_bypass():
    admin = AuthPrincipal(
        actor_id=99,
        actor_type=PrincipalType.USER,
        name="Admin",
        role_names=["ADMIN"],
        permissions=set(),
    )

    checker = PermissionChecker("super.sensitive.permission")
    result = checker(admin)
    assert result == admin


def test_get_current_principal_jwt_success():
    from app.utils.password import AccessTokenPayload

    mock_session = MagicMock()
    mock_payload = AccessTokenPayload(
        sub=123,
        type="access",
        name="Test User",
        email="test@dutai.site",
        roles=["LEADER"],
        permissions=["homework.read"],
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.core.deps.decode_access_token", lambda token: mock_payload)

        principal = get_current_principal("mock-valid-jwt", mock_session)

        assert principal.is_user is True
        assert principal.actor_id == 123
        assert principal.user_id == 123
        assert principal.name == "Test User"
        assert principal.email == "test@dutai.site"
        assert principal.role_names == ["LEADER"]
        assert principal.has_permission("homework.read") is True


def test_get_current_principal_api_key_success():
    mock_session = MagicMock()
    mock_key = MagicMock()
    mock_key.id = 7
    mock_key.name = "Bot Sync"
    mock_key.key_hash = "hashed_secret"
    mock_role = MagicMock()
    mock_role.id = 2
    mock_key.role = mock_role

    mock_full_role = MagicMock()
    mock_full_role.name = "SYSTEM"
    mock_perm = MagicMock()
    mock_perm.permission.name = "homework.read"
    mock_full_role.role_permissions = [mock_perm]

    with pytest.MonkeyPatch.context() as mp:
        mock_api_key_repo = MagicMock()
        mock_api_key_repo.get_candidates_by_prefix.return_value = [mock_key]
        mp.setattr("app.core.deps.RoleApiKeyRepository", lambda s: mock_api_key_repo)

        mock_role_repo = MagicMock()
        mock_role_repo.get_role_with_permissions.return_value = mock_full_role
        mp.setattr("app.core.deps.RoleRepository", lambda s: mock_role_repo)

        mp.setattr("app.core.deps.verify_password", lambda token, hash_val: True)

        principal = get_current_principal("sk-1234567890abcdef", mock_session)

        assert principal.is_user is False
        assert principal.is_api_key is True
        assert principal.actor_id == 7
        assert principal.id is None  # user id alias is None for API Key
        assert principal.name == "System: Bot Sync"
        assert principal.role_names == ["SYSTEM"]
        assert principal.has_permission("homework.read") is True
